from types import SimpleNamespace

import litellm
import pytest

from app.ai import llm as modulo
from app.ai.llm import ClienteLiteLLM, ErroConfiguracao, ErroTransitorio


def _resposta_litellm():
    chamada = SimpleNamespace(id="t1", function=SimpleNamespace(name="consultar_backlog", arguments="{}"))
    mensagem = SimpleNamespace(content=None, tool_calls=[chamada], thinking_blocks=[{"type": "thinking", "thinking": "", "signature": "x"}])
    return SimpleNamespace(
        choices=[SimpleNamespace(message=mensagem)], usage=SimpleNamespace(prompt_tokens=50, completion_tokens=7)
    )


async def test_converte_resposta_e_envia_tool_choice_auto(monkeypatch):
    recebido = {}

    async def falso(**kwargs):
        recebido.update(kwargs)
        return _resposta_litellm()

    monkeypatch.setattr(modulo.litellm, "acompletion", falso)
    r = await ClienteLiteLLM(30).completar("anthropic/claude-opus-5-5", [{"role": "user", "content": "oi"}], [])

    assert recebido["tool_choice"] == "auto" and recebido["timeout"] == 30
    assert "temperature" not in recebido
    assert r.mensagem["tool_calls"][0]["function"]["name"] == "consultar_backlog"
    assert r.mensagem["thinking_blocks"]  # preservados para o próximo turno
    assert (r.tokens_entrada, r.tokens_saida) == (50, 7)


@pytest.mark.parametrize(
    "erro, esperado",
    [
        (litellm.Timeout(message="t", model="m", llm_provider="anthropic"), ErroTransitorio),
        (litellm.InternalServerError(message="500", model="m", llm_provider="anthropic"), ErroTransitorio),
        (litellm.AuthenticationError(message="401", model="m", llm_provider="anthropic"), ErroConfiguracao),
    ],
)
async def test_mapeia_erros_do_litellm(monkeypatch, erro, esperado):
    async def falso(**_):
        raise erro

    monkeypatch.setattr(modulo.litellm, "acompletion", falso)
    with pytest.raises(esperado):
        await ClienteLiteLLM(30).completar("m", [], [])
