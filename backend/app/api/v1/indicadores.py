from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import FiltroDep
from app.domain import indicadores as ind
from app.services.consultas import RespostaIndicador, ServicoIndicadores

router = APIRouter(prefix="/indicadores", tags=["indicadores"])


def get_servico(request: Request) -> ServicoIndicadores:
    return request.app.state.servico


ServicoDep = Annotated[ServicoIndicadores, Depends(get_servico)]


async def _responder(coro):
    try:
        return await coro
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro


@router.get("/volume", response_model=RespostaIndicador[ind.Volume], summary="IND-01 Volume de chamados")
async def volume(servico: ServicoDep, filtro: FiltroDep, granularidade: ind.Granularidade = "dia"):
    return await _responder(servico.volume(filtro, granularidade))


@router.get("/backlog", response_model=RespostaIndicador[ind.Backlog], summary="IND-02 Backlog e aging")
async def backlog(servico: ServicoDep, filtro: FiltroDep):
    """Fotografia dos chamados abertos na data de referência; o período não se aplica."""
    return await _responder(servico.backlog(filtro))


@router.get("/sla_tto", response_model=RespostaIndicador[ind.Sla], summary="IND-03 Cumprimento de SLA de atendimento")
async def sla_tto(servico: ServicoDep, filtro: FiltroDep, dimensao: ind.Dimensao | None = None):
    return await _responder(servico.sla(filtro, "tto", dimensao))


@router.get("/sla_ttr", response_model=RespostaIndicador[ind.Sla], summary="IND-04 Cumprimento de SLA de solução")
async def sla_ttr(servico: ServicoDep, filtro: FiltroDep, dimensao: ind.Dimensao | None = None):
    return await _responder(servico.sla(filtro, "ttr", dimensao))


@router.get(
    "/sla_em_risco", response_model=RespostaIndicador[ind.SlaEmRisco], summary="IND-05 SLA vencido ou em risco"
)
async def sla_em_risco(
    servico: ServicoDep, filtro: FiltroDep, limite: Annotated[int, Query(ge=1, le=500)] = 50
):
    """Fotografia dos chamados abertos na data de referência; o período não se aplica."""
    return await _responder(servico.sla_em_risco(filtro, limite))


@router.get("/tempos", response_model=RespostaIndicador[ind.Tempos], summary="IND-06 Tempos de atendimento e solução")
async def tempos(servico: ServicoDep, filtro: FiltroDep):
    return await _responder(servico.tempos(filtro))


@router.get(
    "/distribuicao", response_model=RespostaIndicador[ind.Distribuicao], summary="IND-07 Distribuição por dimensão"
)
async def distribuicao(
    servico: ServicoDep,
    filtro: FiltroDep,
    dimensao: ind.Dimensao = "categoria",
    top_n: Annotated[int, Query(ge=1, le=50)] = 10,
):
    return await _responder(servico.distribuicao(filtro, dimensao, top_n))


filtros_router = APIRouter(prefix="/filtros", tags=["filtros"])


@filtros_router.get("/valores", response_model=ind.ValoresFiltro, summary="Valores válidos para os filtros")
async def valores(servico: ServicoDep):
    return await servico.valores_filtro()
