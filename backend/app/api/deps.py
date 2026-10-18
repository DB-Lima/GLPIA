from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request

from app.domain.models import FiltroChamados, TipoChamado
from app.domain.ports import GlpiPort


def get_glpi(request: Request) -> GlpiPort:
    return request.app.state.glpi


def get_filtro(
    periodo_inicio: date | None = None,
    periodo_fim: date | None = None,
    grupo_tecnico: str | None = None,
    categoria: str | None = None,
    incluir_subcategorias: bool = True,
    prioridade: Annotated[int | None, Query(ge=1, le=6)] = None,
    tipo: TipoChamado | None = None,
    entidade: str | None = None,
) -> FiltroChamados:
    try:
        return FiltroChamados(
            periodo_inicio=periodo_inicio,
            periodo_fim=periodo_fim,
            grupo_tecnico=grupo_tecnico,
            categoria=categoria,
            incluir_subcategorias=incluir_subcategorias,
            prioridade=prioridade,
            tipo=tipo,
            entidade=entidade,
        )
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro


GlpiDep = Annotated[GlpiPort, Depends(get_glpi)]
FiltroDep = Annotated[FiltroChamados, Depends(get_filtro)]
