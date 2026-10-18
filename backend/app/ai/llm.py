"""Acesso ao LLM via LiteLLM (router corporativo, ADR-0003)."""

from dataclasses import dataclass
from typing import Protocol

import litellm

litellm.drop_params = True  # descarta parâmetros que o provedor não aceita, em vez de falhar

ERROS_TRANSITORIOS = (
    litellm.Timeout,
    litellm.APIConnectionError,
    litellm.InternalServerError,
    litellm.ServiceUnavailableError,
    litellm.BadGatewayError,
)
ERROS_CONFIGURACAO = (litellm.AuthenticationError, litellm.PermissionDeniedError, litellm.NotFoundError)


class ErroTransitorio(Exception):
    """Timeout, falha de conexão ou 5xx: vale tentar o modelo de fallback."""


class ErroConfiguracao(Exception):
    """Chave ausente/inválida ou modelo inexistente: o fallback não resolve."""


@dataclass
class RespostaLLM:
    mensagem: dict
    modelo: str
    tokens_entrada: int
    tokens_saida: int


class ClienteLLM(Protocol):
    async def completar(self, modelo: str, mensagens: list[dict], ferramentas: list[dict]) -> RespostaLLM: ...


class ClienteLiteLLM:
    def __init__(self, timeout_segundos: float):
        self._timeout = timeout_segundos

    async def completar(self, modelo: str, mensagens: list[dict], ferramentas: list[dict]) -> RespostaLLM:
        try:
            resposta = await litellm.acompletion(
                model=modelo,
                messages=mensagens,
                tools=ferramentas,
                tool_choice="auto",  # escolha forçada de ferramenta não é aceita pelos modelos Claude atuais
                timeout=self._timeout,
                max_tokens=16000,
            )
        except ERROS_CONFIGURACAO as erro:
            raise ErroConfiguracao(str(erro)) from erro
        except ERROS_TRANSITORIOS as erro:
            raise ErroTransitorio(str(erro)) from erro

        mensagem = resposta.choices[0].message
        dados: dict = {"role": "assistant", "content": mensagem.content}
        if mensagem.tool_calls:
            dados["tool_calls"] = [
                {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                for c in mensagem.tool_calls
            ]
        # Blocos de raciocínio precisam voltar intactos no próximo turno quando há uso de ferramentas.
        if getattr(mensagem, "thinking_blocks", None):
            dados["thinking_blocks"] = mensagem.thinking_blocks
        uso = getattr(resposta, "usage", None)
        return RespostaLLM(
            mensagem=dados,
            modelo=modelo,
            tokens_entrada=getattr(uso, "prompt_tokens", 0) or 0,
            tokens_saida=getattr(uso, "completion_tokens", 0) or 0,
        )
