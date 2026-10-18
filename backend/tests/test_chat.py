"""Testes do chat com LLM simulado: nenhum teste chama a API real."""

import json
import logging

import pytest

from app.ai.agente import Agente
from app.ai.llm import ErroConfiguracao, ErroTransitorio, RespostaLLM
from app.logs import obter_logger

N2 = "N2 - Suporte Técnico"
SETEMBRO = {"periodo_inicio": "2026-09-01", "periodo_fim": "2026-09-30"}


def _assistente(*chamadas: tuple[str, dict], texto: str | None = None) -> dict:
    msg = {"role": "assistant", "content": texto}
    if chamadas:
        msg["tool_calls"] = [
            {"id": f"c{i}", "type": "function", "function": {"name": nome, "arguments": json.dumps(args)}}
            for i, (nome, args) in enumerate(chamadas)
        ]
    return msg


def _ultimo_resultado(mensagens: list[dict]) -> dict:
    resultados = [json.loads(m["content"]) for m in mensagens if m["role"] == "tool"]
    com_dados = [r for r in resultados if "resultado" in r]
    return (com_dados or resultados)[-1]


class LLMFalso:
    """Executa um roteiro: cada passo é uma função (mensagens) -> mensagem do assistente, ou uma exceção."""

    def __init__(self, roteiro, falhas: dict[str, Exception] | None = None):
        self.roteiro = list(roteiro)
        self.falhas = falhas or {}
        self.chamadas: list[tuple[str, list[dict]]] = []

    async def completar(self, modelo, mensagens, ferramentas):
        self.chamadas.append((modelo, json.loads(json.dumps(mensagens))))
        if modelo in self.falhas:
            raise self.falhas[modelo]
        passo = self.roteiro.pop(0)
        return RespostaLLM(mensagem=passo(mensagens), modelo=modelo, tokens_entrada=100, tokens_saida=20)


@pytest.fixture
def com_llm(client):
    def configurar(roteiro, falhas=None, modelos=("principal", "reserva")):
        llm = LLMFalso(roteiro, falhas)
        client.app.state.agente = Agente(client.app.state.servico, llm, list(modelos))
        return llm

    return configurar


@pytest.fixture
def logs():
    registros: list[logging.LogRecord] = []

    class Lista(logging.Handler):
        def emit(self, record):
            registros.append(record)

    logger = obter_logger()
    handler = Lista()
    logger.addHandler(handler)
    yield registros
    logger.removeHandler(handler)


def _perguntar(client, pergunta, **extra):
    return client.post("/api/v1/chat", json={"pergunta": pergunta, **extra})


def roteiro_sla_n2():
    args = {"tipo_sla": "ttr", "grupo_tecnico": N2, **SETEMBRO}

    def responder(mensagens):
        r = _ultimo_resultado(mensagens)["resultado"]
        texto = f"Em setembro o N2 cumpriu {r['percentual']}% do SLA de solução ({r['cumpridos']} de {r['elegiveis']})."
        return _assistente(("responder_usuario", {
            "resposta": texto,
            "visualizacao": {"chamada": 1, "titulo": "SLA de solução do N2 em setembro"},
            "filtros_sugeridos": {"grupo_tecnico": N2, **SETEMBRO},
        }))

    return [lambda m: _assistente(("consultar_sla", args)), responder]


def test_percentual_do_chat_bate_com_o_endpoint(client, com_llm):
    com_llm(roteiro_sla_n2())
    corpo = _perguntar(client, "Qual o SLA de solução do N2 em setembro?").json()
    esperado = client.get("/api/v1/indicadores/sla_ttr", params={"grupo_tecnico": N2, **SETEMBRO}).json()["resultado"]

    assert f"{esperado['percentual']}%" in corpo["resposta"]
    kpis = {k["rotulo"]: k["valor"] for k in corpo["visualizacao"]["kpis"]}
    assert kpis["Cumprido"] == esperado["percentual"]
    assert kpis["Elegíveis"] == esperado["elegiveis"]
    assert corpo["filtros_sugeridos"] == {"grupo_tecnico": N2, **SETEMBRO}
    assert corpo["modelo"] == "principal" and len(corpo["trace_id"]) == 32


def test_resposta_numerica_tem_rastreio(client, com_llm):
    com_llm(roteiro_sla_n2())
    corpo = _perguntar(client, "SLA do N2?").json()
    assert corpo["rastreio"] == [
        {"chamada": 1, "ferramenta": "consultar_sla", "argumentos": {"tipo_sla": "ttr", "grupo_tecnico": N2, **SETEMBRO}}
    ]


def test_numero_sem_ferramenta_e_rejeitado(client, com_llm):
    inventado = lambda m: _assistente(("responder_usuario", {"resposta": "O SLA foi de 93%."}))
    com_llm([inventado, inventado])
    resposta = _perguntar(client, "Qual o SLA?")
    assert resposta.status_code == 502


def test_payload_para_o_llm_nao_tem_titulo_nem_email(client, com_llm, dados_mock):
    llm = com_llm([
        lambda m: _assistente(("listar_sla_em_risco", {"limite": 20}), ("consultar_volume", SETEMBRO)),
        lambda m: _assistente(("responder_usuario", {"resposta": "Há chamados vencidos.", "visualizacao": {"chamada": 1, "titulo": "Em risco"}})),
    ])
    corpo = _perguntar(client, "Quais chamados estão com SLA vencido?").json()

    enviado = json.dumps([m for _, msgs in llm.chamadas for m in msgs], ensure_ascii=False)
    titulos = {t["name"] for t in dados_mock["tickets"]}
    assert not [t for t in titulos if t in enviado]
    assert "@" not in enviado
    # o resultado chegou ao LLM, só que sem os títulos
    risco = json.loads(next(m for m in llm.chamadas[-1][1] if m["role"] == "tool")["content"])
    assert risco["chamada"] == 1 and risco["resultado"]["itens"]
    assert all("titulo" not in item for item in risco["resultado"]["itens"])
    # o painel recebe os títulos na visualização
    assert any(linha[1] in titulos for linha in corpo["visualizacao"]["linhas"])


def test_email_e_cpf_sao_redigidos_antes_do_llm(client, com_llm, logs):
    llm = com_llm([lambda m: _assistente(("responder_usuario", {"resposta": "Esse dado não está disponível no GLPIA."}))])
    _perguntar(
        client,
        "O chamado de joao.silva@empresa.com.br, CPF 123.456.789-09, estourou o SLA?",
        historico=[{"papel": "usuario", "texto": "meu outro e-mail é ana@teste.io"}],
    )
    enviado = json.dumps(llm.chamadas[0][1], ensure_ascii=False)
    assert "joao.silva@empresa.com.br" not in enviado and "123.456.789-09" not in enviado and "ana@teste.io" not in enviado
    assert "[e-mail removido]" in enviado and "[CPF removido]" in enviado
    redacao = [r for r in logs if r.getMessage() == "redacao_aplicada"]
    assert redacao and redacao[0].dados["substituicoes"] == 3


def test_pergunta_fora_do_catalogo_nao_inventa_numero(client, com_llm):
    com_llm([lambda m: _assistente(("responder_usuario", {
        "resposta": "Não tenho acesso ao conteúdo dos chamados. Posso mostrar volume, backlog, SLA e tempos.",
    }))])
    corpo = _perguntar(client, "Quais chamados falam de VPN?").json()
    assert corpo["rastreio"] == [] and corpo["visualizacao"] is None
    assert "Não tenho acesso" in corpo["resposta"]


def test_timeout_no_principal_usa_fallback(client, com_llm):
    llm = com_llm(roteiro_sla_n2(), falhas={"principal": ErroTransitorio("timeout")})
    corpo = _perguntar(client, "SLA do N2 em setembro?").json()
    assert corpo["modelo"] == "reserva"
    assert [m for m, _ in llm.chamadas] == ["principal", "reserva", "reserva"]  # fica no fallback até o fim


def test_falha_nos_dois_modelos_retorna_503(client, com_llm):
    com_llm([], falhas={"principal": ErroTransitorio("500"), "reserva": ErroTransitorio("503")})
    resposta = _perguntar(client, "SLA?")
    assert resposta.status_code == 503
    assert "indisponível" in resposta.json()["detail"]


def test_chave_invalida_retorna_503_de_configuracao(client, com_llm):
    com_llm([], falhas={"principal": ErroConfiguracao("401")})
    resposta = _perguntar(client, "SLA?")
    assert resposta.status_code == 503
    assert "configurado" in resposta.json()["detail"]


def test_log_registra_trace_modelo_e_tokens(client, com_llm, logs):
    com_llm(roteiro_sla_n2())
    corpo = _perguntar(client, "SLA do N2?").json()
    registro = next(r for r in logs if r.getMessage() == "chat")
    assert registro.dados["trace_id"] == corpo["trace_id"]
    assert registro.dados["modelo"] == "principal"
    assert (registro.dados["tokens_entrada"], registro.dados["tokens_saida"]) == (200, 40)


def test_responder_junto_com_outra_ferramenta_e_corrigido(client, com_llm):
    precipitado = lambda m: _assistente(
        ("consultar_backlog", {}), ("responder_usuario", {"resposta": "Backlog alto."})
    )
    correto = lambda m: _assistente(("responder_usuario", {
        "resposta": f"O backlog atual é de {_ultimo_resultado(m)['resultado']['total']} chamados.",
        "visualizacao": {"chamada": 1, "titulo": "Backlog"},
    }))
    com_llm([precipitado, correto])
    corpo = _perguntar(client, "Qual o backlog?").json()
    assert corpo["visualizacao"]["tipo"] == "barra"
    assert corpo["rastreio"][0]["ferramenta"] == "consultar_backlog"


def test_texto_livre_sem_responder_recebe_uma_correcao(client, com_llm):
    com_llm([
        lambda m: _assistente(texto="Não sei."),
        lambda m: _assistente(("responder_usuario", {"resposta": "Esse dado não está disponível."})),
    ])
    assert _perguntar(client, "Previsão para dezembro?").status_code == 200


def test_argumentos_invalidos_voltam_como_erro_para_o_llm(client, com_llm):
    def corrigir(mensagens):
        assert "erro" in _ultimo_resultado(mensagens)
        return _assistente(("consultar_distribuicao", {"dimensao": "categoria"}))

    com_llm([
        lambda m: _assistente(("consultar_distribuicao", {"dimensao": "cor"})),
        corrigir,
        lambda m: _assistente(("responder_usuario", {"resposta": "Veja a distribuição.", "visualizacao": {"chamada": 1, "titulo": "Categorias"}})),
    ])
    corpo = _perguntar(client, "Distribuição por categoria").json()
    assert corpo["rastreio"][0]["argumentos"]["dimensao"] == "categoria"


def test_ferramentas_expostas_sao_somente_leitura():
    from app.ai.ferramentas import FERRAMENTAS, definicoes_ferramentas

    nomes = {d["function"]["name"] for d in definicoes_ferramentas()}
    assert nomes == set(FERRAMENTAS) | {"responder_usuario"}
    assert all(n.startswith(("consultar_", "listar_")) for n in FERRAMENTAS)
    assert all("$ref" not in json.dumps(d) for d in definicoes_ferramentas())


def test_conta_sem_creditos_retorna_mensagem_clara(client, com_llm):
    com_llm([], falhas={"principal": ErroConfiguracao("credit balance is too low", motivo="creditos")})
    resposta = _perguntar(client, "SLA?")
    assert resposta.status_code == 503 and "sem créditos" in resposta.json()["detail"]


def test_requisicao_recusada_retorna_502(client, com_llm):
    from app.ai.llm import ErroRequisicao

    com_llm([], falhas={"principal": ErroRequisicao("400 invalid schema")})
    assert _perguntar(client, "SLA?").status_code == 502
