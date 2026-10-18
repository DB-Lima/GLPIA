from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.ai.agente import Agente, IndisponivelError, MensagemHistorico, RespostaChat, SaidaInvalidaError
from app.ai.ferramentas import ArgsFiltro
from app.ai.llm import ErroConfiguracao, ErroRequisicao

router = APIRouter(tags=["chat"])


class PerguntaChat(BaseModel):
    pergunta: str = Field(min_length=1, max_length=2000)
    historico: list[MensagemHistorico] = Field(default_factory=list, max_length=20)
    filtros_ativos: ArgsFiltro | None = None


@router.post("/chat", response_model=RespostaChat, summary="Pergunta em linguagem natural ao assistente de IA")
async def chat(request: Request, corpo: PerguntaChat) -> RespostaChat:
    agente: Agente = request.app.state.agente
    try:
        return await agente.responder(corpo.pergunta, corpo.historico, corpo.filtros_ativos)
    except ErroConfiguracao as erro:
        detalhe = (
            "A conta da API de IA está sem créditos. Adicione créditos no console do provedor e tente novamente."
            if erro.motivo == "creditos"
            else "O assistente de IA não está configurado. Verifique a chave da API e o modelo no arquivo .env."
        )
        raise HTTPException(status_code=503, detail=detalhe) from erro
    except ErroRequisicao as erro:
        raise HTTPException(
            status_code=502, detail="A API de IA recusou a requisição. Detalhes no log do backend (trace no evento chat)."
        ) from erro
    except IndisponivelError as erro:
        raise HTTPException(
            status_code=503, detail="O assistente de IA está indisponível no momento. Tente novamente em instantes."
        ) from erro
    except SaidaInvalidaError as erro:
        raise HTTPException(
            status_code=502, detail="Não consegui montar uma resposta confiável para essa pergunta. Tente reformular."
        ) from erro
