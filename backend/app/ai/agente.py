"""Loop de tool calling do assistente: pergunta → ferramentas somente leitura → resposta estruturada."""

import json
import re
import time
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.ai.ferramentas import (
    FERRAMENTAS,
    RESPONDER,
    ArgsFiltro,
    ArgsResponder,
    Visualizacao,
    definicoes_ferramentas,
    montar_visualizacao,
    para_llm,
)
from app.ai.llm import ClienteLLM, ErroConfiguracao, ErroTransitorio
from app.ai.redacao import redigir
from app.logs import obter_logger
from app.services.consultas import ServicoIndicadores

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
MAX_PASSOS = 8
MAX_CORRECOES = 1
logger = obter_logger()


class IndisponivelError(Exception):
    """Modelo principal e fallback indisponíveis."""


class SaidaInvalidaError(Exception):
    """O modelo não produziu uma resposta no formato esperado, mesmo após correção."""


class MensagemHistorico(BaseModel):
    papel: Literal["usuario", "assistente"]
    texto: str = Field(max_length=4000)


class ItemRastreio(BaseModel):
    chamada: int
    ferramenta: str
    argumentos: dict


class RespostaChat(BaseModel):
    resposta: str
    visualizacao: Visualizacao | None
    filtros_sugeridos: dict | None
    rastreio: list[ItemRastreio]
    trace_id: str
    modelo: str


@lru_cache
def carregar_prompt(versao: str = "system_v1") -> str:
    return yaml.safe_load((PROMPTS_DIR / f"{versao}.yaml").read_text(encoding="utf-8"))["texto"]


def _resultado_ferramenta(id_chamada: str, conteudo: dict) -> dict:
    return {"role": "tool", "tool_call_id": id_chamada, "content": json.dumps(conteudo, ensure_ascii=False)}


class Agente:
    def __init__(self, servico: ServicoIndicadores, llm: ClienteLLM, modelos: list[str]):
        self._servico = servico
        self._llm = llm
        self._modelos = [m for m in modelos if m]
        self._ferramentas = definicoes_ferramentas()

    async def _completar(self, estado: dict, mensagens: list[dict]):
        """Usa o modelo atual; em erro transitório passa ao próximo e fica nele até o fim da pergunta."""
        while estado["indice_modelo"] < len(self._modelos):
            modelo = self._modelos[estado["indice_modelo"]]
            try:
                return await self._llm.completar(modelo, mensagens, self._ferramentas)
            except ErroTransitorio as erro:
                logger.warning("llm_falhou", extra={"dados": {"trace_id": estado["trace_id"], "modelo": modelo, "erro": str(erro)[:300]}})
                estado["indice_modelo"] += 1
        raise IndisponivelError("Nenhum modelo de IA disponível")

    async def responder(
        self, pergunta: str, historico: list[MensagemHistorico], filtros_ativos: ArgsFiltro | None
    ) -> RespostaChat:
        trace_id = uuid.uuid4().hex
        inicio = time.perf_counter()
        estado = {"trace_id": trace_id, "indice_modelo": 0}

        redacoes = 0
        mensagens: list[dict] = [{"role": "system", "content": carregar_prompt()}]
        for item in historico[-10:]:
            texto, n = redigir(item.texto)
            redacoes += n
            mensagens.append({"role": "user" if item.papel == "usuario" else "assistant", "content": texto})
        pergunta_limpa, n = redigir(pergunta)
        redacoes += n
        if redacoes:
            logger.info("redacao_aplicada", extra={"dados": {"trace_id": trace_id, "substituicoes": redacoes}})

        filtros = filtros_ativos.model_dump(mode="json", exclude_none=True) if filtros_ativos else {}
        contexto = (
            f"Data de referência dos dados: {self._servico.referencia().isoformat()}.\n"
            f"Filtros ativos no painel: {json.dumps(filtros, ensure_ascii=False) if filtros else 'nenhum'}.\n\n"
        )
        mensagens.append({"role": "user", "content": contexto + pergunta_limpa})

        rastreio: list[ItemRastreio] = []
        resultados: dict[int, tuple] = {}  # chamada -> (ferramenta, resultado completo)
        tokens_entrada = tokens_saida = 0
        correcoes = 0
        modelo_usado = ""
        final: ArgsResponder | None = None

        try:
            for _ in range(MAX_PASSOS):
                r = await self._completar(estado, mensagens)
                modelo_usado = r.modelo
                tokens_entrada += r.tokens_entrada
                tokens_saida += r.tokens_saida
                mensagens.append(r.mensagem)
                chamadas = r.mensagem.get("tool_calls") or []

                if not chamadas:
                    correcoes += 1
                    if correcoes > MAX_CORRECOES:
                        raise SaidaInvalidaError("modelo respondeu sem chamar responder_usuario")
                    mensagens.append({"role": "user", "content": "Entregue a resposta final chamando a ferramenta responder_usuario."})
                    continue

                respostas_ferramentas = []
                so_responder = all(c["function"]["name"] == RESPONDER for c in chamadas)
                for chamada in chamadas:
                    nome = chamada["function"]["name"]
                    try:
                        argumentos = json.loads(chamada["function"]["arguments"] or "{}")
                    except json.JSONDecodeError:
                        respostas_ferramentas.append(_resultado_ferramenta(chamada["id"], {"erro": "argumentos não são JSON válido"}))
                        continue

                    if nome == RESPONDER:
                        erro = None
                        if not so_responder:
                            erro = "Chame responder_usuario sozinho, depois de receber os resultados das outras ferramentas."
                        else:
                            try:
                                candidato = ArgsResponder.model_validate(argumentos)
                                if candidato.visualizacao and candidato.visualizacao.chamada not in resultados:
                                    erro = f"visualizacao.chamada {candidato.visualizacao.chamada} não existe"
                                elif re.search(r"\d", candidato.resposta) and not rastreio:
                                    erro = "A resposta contém números, mas nenhuma ferramenta de dados foi chamada."
                                else:
                                    final = candidato
                            except ValidationError as e:
                                erro = f"argumentos inválidos: {e.errors(include_url=False)}"
                        if erro:
                            correcoes += 1
                            if correcoes > MAX_CORRECOES:
                                raise SaidaInvalidaError(erro)
                            respostas_ferramentas.append(_resultado_ferramenta(chamada["id"], {"erro": erro}))
                        continue

                    ferramenta = FERRAMENTAS.get(nome)
                    if ferramenta is None:
                        respostas_ferramentas.append(_resultado_ferramenta(chamada["id"], {"erro": f"ferramenta desconhecida: {nome}"}))
                        continue
                    try:
                        args = ferramenta.argumentos.model_validate(argumentos)
                        resultado = await ferramenta.executar(self._servico, args)
                    except (ValidationError, ValueError) as e:
                        detalhe = e.errors(include_url=False) if isinstance(e, ValidationError) else str(e)
                        respostas_ferramentas.append(_resultado_ferramenta(chamada["id"], {"erro": f"argumentos inválidos: {detalhe}"}))
                        continue

                    numero = len(rastreio) + 1
                    rastreio.append(ItemRastreio(chamada=numero, ferramenta=nome, argumentos=args.model_dump(mode="json", exclude_none=True)))
                    resultados[numero] = (ferramenta, resultado)
                    respostas_ferramentas.append(_resultado_ferramenta(chamada["id"], {"chamada": numero, **para_llm(resultado)}))

                if final:
                    break
                mensagens.extend(respostas_ferramentas)
            else:
                raise SaidaInvalidaError("limite de passos atingido")
        except ErroConfiguracao:
            self._registrar(trace_id, inicio, modelo_usado, tokens_entrada, tokens_saida, rastreio, "erro_configuracao")
            raise
        except (IndisponivelError, SaidaInvalidaError) as erro:
            self._registrar(trace_id, inicio, modelo_usado, tokens_entrada, tokens_saida, rastreio, type(erro).__name__)
            raise

        visualizacao = None
        if final.visualizacao:
            ferramenta, resultado = resultados[final.visualizacao.chamada]
            visualizacao = montar_visualizacao(ferramenta, resultado, final.visualizacao.titulo)
        filtros_sugeridos = None
        if final.filtros_sugeridos:
            filtros_sugeridos = final.filtros_sugeridos.model_dump(mode="json", exclude_none=True) or None

        self._registrar(trace_id, inicio, modelo_usado, tokens_entrada, tokens_saida, rastreio, "ok")
        return RespostaChat(
            resposta=final.resposta,
            visualizacao=visualizacao,
            filtros_sugeridos=filtros_sugeridos,
            rastreio=rastreio,
            trace_id=trace_id,
            modelo=modelo_usado,
        )

    @staticmethod
    def _registrar(trace_id, inicio, modelo, tokens_entrada, tokens_saida, rastreio, situacao) -> None:
        logger.info(
            "chat",
            extra={
                "dados": {
                    "trace_id": trace_id,
                    "situacao": situacao,
                    "modelo": modelo,
                    "tokens_entrada": tokens_entrada,
                    "tokens_saida": tokens_saida,
                    "ferramentas": [i.ferramenta for i in rastreio],
                    "duracao_ms": round((time.perf_counter() - inicio) * 1000),
                }
            },
        )
