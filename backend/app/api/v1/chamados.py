from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import FiltroDep, GlpiDep
from app.domain.models import Chamado, FiltroChamados

router = APIRouter(prefix="/chamados", tags=["chamados"])


class AmostraChamados(BaseModel):
    total: int
    itens: list[Chamado]
    filtro_aplicado: FiltroChamados


@router.get("/amostra", response_model=AmostraChamados)
async def amostra(
    glpi: GlpiDep,
    filtro: FiltroDep,
    limite: Annotated[int, Query(ge=1, le=100)] = 10,
) -> AmostraChamados:
    """Amostra dos chamados mais recentes que atendem ao filtro (apoio a desenvolvimento e depuração)."""
    chamados = await glpi.listar_chamados(filtro)
    recentes = sorted(chamados, key=lambda c: c.aberto_em, reverse=True)[:limite]
    return AmostraChamados(total=len(chamados), itens=recentes, filtro_aplicado=filtro)
