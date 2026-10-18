"""Modelo normalizado de chamado, independente da versão do GLPI (ver agent_docs/glpi-dominio.md)."""

from datetime import date, datetime
from enum import IntEnum
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, model_validator

FUSO = ZoneInfo("America/Sao_Paulo")


class StatusChamado(IntEnum):
    NOVO = 1
    EM_ATENDIMENTO_ATRIBUIDO = 2
    EM_ATENDIMENTO_PLANEJADO = 3
    PENDENTE = 4
    SOLUCIONADO = 5
    FECHADO = 6

    @property
    def aberto(self) -> bool:
        return self <= StatusChamado.PENDENTE


TipoChamado = Literal["incidente", "requisicao"]


class Chamado(BaseModel):
    id: int
    entidade: str
    # Exibido só no painel; nunca enviado ao LLM (ADR-0004).
    titulo: str
    aberto_em: datetime
    assumido_em: datetime | None
    solucionado_em: datetime | None
    fechado_em: datetime | None
    status: StatusChamado
    tipo: TipoChamado
    prioridade: int = Field(ge=1, le=6)
    categoria: str | None
    grupos_tecnicos: list[str]
    prazo_tto: datetime | None
    prazo_ttr: datetime | None
    segundos_ate_assumir: int | None
    segundos_ate_solucionar: int | None
    excluido: bool


class FiltroChamados(BaseModel):
    """Filtros comuns de docs/01-indicadores.md. Período compara a data de abertura."""

    periodo_inicio: date | None = None
    periodo_fim: date | None = None
    grupo_tecnico: str | None = None
    categoria: str | None = None
    incluir_subcategorias: bool = True
    prioridade: int | None = Field(default=None, ge=1, le=6)
    tipo: TipoChamado | None = None
    entidade: str | None = None
    incluir_excluidos: bool = False

    @model_validator(mode="after")
    def _periodo_valido(self) -> "FiltroChamados":
        if self.periodo_inicio and self.periodo_fim and self.periodo_inicio > self.periodo_fim:
            raise ValueError("periodo_inicio deve ser anterior ou igual a periodo_fim")
        return self
