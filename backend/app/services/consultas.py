"""Orquestra as consultas de indicadores: período padrão, leitura do GLPI e cache.

Usado pela API REST e pelas ferramentas da IA, para que os dois devolvam os mesmos números.
"""

import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Generic, TypeVar

from pydantic import BaseModel

from app.domain import indicadores as ind
from app.domain.models import FUSO, Chamado, FiltroChamados
from app.domain.ports import GlpiPort

T = TypeVar("T", bound=BaseModel)
DIAS_PERIODO_PADRAO = 30
TTL_CACHE_SEGUNDOS = 300


class RespostaIndicador(BaseModel, Generic[T]):
    filtro_aplicado: FiltroChamados
    referencia: datetime
    resultado: T


class CacheTTL:
    def __init__(self, ttl_segundos: float = TTL_CACHE_SEGUNDOS):
        self._ttl = ttl_segundos
        self._itens: dict[str, tuple[float, object]] = {}

    def obter(self, chave: str):
        item = self._itens.get(chave)
        if item and time.monotonic() - item[0] < self._ttl:
            return item[1]
        return None

    def gravar(self, chave: str, valor: object) -> None:
        self._itens[chave] = (time.monotonic(), valor)

    def limpar(self) -> None:
        self._itens.clear()


class ServicoIndicadores:
    def __init__(self, glpi: GlpiPort, cache: CacheTTL | None = None):
        self._glpi = glpi
        self.cache = cache or CacheTTL()

    def referencia(self) -> datetime:
        return self._glpi.agora()

    def filtro_efetivo(self, filtro: FiltroChamados) -> FiltroChamados:
        """Preenche o período padrão (últimos 30 dias até a data de referência)."""
        fim = filtro.periodo_fim or self._glpi.agora().astimezone(FUSO).date()
        inicio = filtro.periodo_inicio or fim - timedelta(days=DIAS_PERIODO_PADRAO - 1)
        if inicio > fim:
            raise ValueError("periodo_inicio deve ser anterior ou igual a periodo_fim")
        return filtro.model_copy(update={"periodo_inicio": inicio, "periodo_fim": fim})

    async def _executar(
        self,
        nome: str,
        modelo: type[T],
        filtro: FiltroChamados,
        calcular: Callable[[list[Chamado], ind.Periodo, datetime], T],
        **parametros,
    ) -> RespostaIndicador[T]:
        efetivo = self.filtro_efetivo(filtro)
        chave = f"{nome}|{efetivo.model_dump_json()}|{sorted(parametros.items())}"
        if (em_cache := self.cache.obter(chave)) is not None:
            return em_cache

        # O período é aplicado por indicador (cada um usa uma data diferente), então
        # o GLPI é consultado só com as demais dimensões.
        sem_periodo = efetivo.model_copy(update={"periodo_inicio": None, "periodo_fim": None})
        chamados = await self._glpi.listar_chamados(sem_periodo)
        periodo = ind.Periodo(inicio=efetivo.periodo_inicio, fim=efetivo.periodo_fim)
        agora = self._glpi.agora()
        # Parametriza com a classe concreta para a serialização não perder campos.
        resposta = RespostaIndicador[modelo](
            filtro_aplicado=efetivo, referencia=agora, resultado=calcular(chamados, periodo, agora)
        )
        self.cache.gravar(chave, resposta)
        return resposta

    async def volume(self, filtro: FiltroChamados, granularidade: ind.Granularidade = "dia"):
        return await self._executar(
            "volume", ind.Volume, filtro, lambda c, p, _: ind.volume(c, p, granularidade), granularidade=granularidade
        )

    async def backlog(self, filtro: FiltroChamados):
        return await self._executar("backlog", ind.Backlog, filtro, lambda c, _, agora: ind.backlog(c, agora))

    async def sla(self, filtro: FiltroChamados, tipo: ind.TipoSla, dimensao: ind.Dimensao | None = None):
        return await self._executar(
            "sla", ind.Sla, filtro, lambda c, p, _: ind.sla(c, p, tipo, dimensao), tipo=tipo, dimensao=dimensao
        )

    async def sla_em_risco(self, filtro: FiltroChamados, limite: int = 50):
        return await self._executar(
            "sla_em_risco", ind.SlaEmRisco, filtro, lambda c, _, agora: ind.sla_em_risco(c, agora, limite), limite=limite
        )

    async def tempos(self, filtro: FiltroChamados):
        return await self._executar("tempos", ind.Tempos, filtro, lambda c, p, _: ind.tempos(c, p))

    async def distribuicao(self, filtro: FiltroChamados, dimensao: ind.Dimensao, top_n: int = 10):
        return await self._executar(
            "distribuicao", ind.Distribuicao, filtro, lambda c, p, _: ind.distribuicao(c, p, dimensao, top_n),
            dimensao=dimensao, top_n=top_n,
        )

    async def valores_filtro(self) -> ind.ValoresFiltro:
        chamados = await self._glpi.listar_chamados(FiltroChamados())
        return ind.valores_filtro(chamados)
