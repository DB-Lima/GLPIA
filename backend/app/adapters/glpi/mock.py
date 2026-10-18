"""Adapter mock: lê um JSON com tabelas no formato do GLPI e converte para o modelo normalizado."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.filtros import filtrar
from app.domain.models import FUSO, Chamado, FiltroChamados, StatusChamado

GRUPO_ATRIBUIDO = 2  # glpi_groups_tickets.type
TIPOS = {1: "incidente", 2: "requisicao"}


def _data(valor: str | None) -> datetime | None:
    # O GLPI grava datas sem fuso, no horário local da instância.
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d %H:%M:%S").replace(tzinfo=FUSO)


def _por_id(linhas: list[dict[str, Any]]) -> dict[int, str]:
    return {linha["id"]: linha["completename"] for linha in linhas}


def converter(dados: dict[str, Any]) -> list[Chamado]:
    entidades = _por_id(dados["entities"])
    grupos = _por_id(dados["groups"])
    categorias = _por_id(dados["itilcategories"])

    grupos_por_chamado: dict[int, list[str]] = {}
    for vinculo in dados["groups_tickets"]:
        if vinculo["type"] == GRUPO_ATRIBUIDO:
            grupos_por_chamado.setdefault(vinculo["tickets_id"], []).append(grupos[vinculo["groups_id"]])

    return [
        Chamado(
            id=t["id"],
            entidade=entidades[t["entities_id"]],
            titulo=t["name"],
            aberto_em=_data(t["date"]),
            assumido_em=_data(t["takeintoaccountdate"]),
            solucionado_em=_data(t["solvedate"]),
            fechado_em=_data(t["closedate"]),
            status=StatusChamado(t["status"]),
            tipo=TIPOS[t["type"]],
            prioridade=t["priority"],
            categoria=categorias.get(t["itilcategories_id"]),
            grupos_tecnicos=sorted(grupos_por_chamado.get(t["id"], [])),
            prazo_tto=_data(t["time_to_own"]),
            prazo_ttr=_data(t["time_to_resolve"]),
            segundos_ate_assumir=t["takeintoaccount_delay_stat"] or None,
            segundos_ate_solucionar=t["solve_delay_stat"] or None,
            excluido=bool(t["is_deleted"]),
        )
        for t in dados["tickets"]
    ]


class MockGlpiAdapter:
    def __init__(self, caminho: Path):
        self._caminho = caminho
        self._chamados: list[Chamado] | None = None

    def _carregar(self) -> list[Chamado]:
        if self._chamados is None:
            if not self._caminho.exists():
                raise FileNotFoundError(
                    f"Dataset mock não encontrado em {self._caminho}. Rode: python scripts/gerar_mock.py"
                )
            self._chamados = converter(json.loads(self._caminho.read_text(encoding="utf-8")))
        return self._chamados

    async def listar_chamados(self, filtro: FiltroChamados) -> list[Chamado]:
        return filtrar(self._carregar(), filtro)
