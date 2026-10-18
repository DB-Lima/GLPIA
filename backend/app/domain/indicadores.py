"""Fórmulas dos indicadores IND-01 a IND-07. Fonte da verdade: docs/01-indicadores.md.

Funções puras: recebem chamados já filtrados pelas dimensões (grupo, categoria, ...)
e aplicam o período sobre a data relevante de cada indicador.
"""

import math
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel

from app.domain.models import FUSO, Chamado

Dimensao = Literal["categoria", "grupo_tecnico", "prioridade", "tipo", "entidade"]
Granularidade = Literal["dia", "semana", "mes"]
TipoSla = Literal["tto", "ttr"]

SEM_GRUPO = "Sem grupo"
SEM_CATEGORIA = "Sem categoria"
NOMES_PRIORIDADE = {1: "1 - Muito baixa", 2: "2 - Baixa", 3: "3 - Média", 4: "4 - Alta", 5: "5 - Muito alta", 6: "6 - Crítica"}
FAIXAS_AGING: list[tuple[str, int, int | None]] = [
    ("0-2 d", 0, 2),
    ("3-7 d", 3, 7),
    ("8-15 d", 8, 15),
    ("16-30 d", 16, 30),
    ("> 30 d", 31, None),
]
LIMIAR_RISCO = 0.20  # fração do prazo total que ainda resta


class Periodo(BaseModel):
    inicio: date
    fim: date

    def contem(self, momento: datetime | None) -> bool:
        return momento is not None and self.inicio <= momento.astimezone(FUSO).date() <= self.fim


# ---------- utilitários ----------

def _pct(cumpridos: int, elegiveis: int) -> float | None:
    return round(100 * cumpridos / elegiveis, 1) if elegiveis else None


def _horas(segundos: float) -> float:
    return round(segundos / 3600, 1)


def valores_dimensao(chamado: Chamado, dimensao: Dimensao) -> list[str]:
    if dimensao == "grupo_tecnico":
        return chamado.grupos_tecnicos or [SEM_GRUPO]
    if dimensao == "categoria":
        return [chamado.categoria or SEM_CATEGORIA]
    if dimensao == "prioridade":
        return [NOMES_PRIORIDADE[chamado.prioridade]]
    if dimensao == "tipo":
        return [chamado.tipo]
    return [chamado.entidade]


def _chave_tempo(dia: date, granularidade: Granularidade) -> str:
    if granularidade == "dia":
        return dia.isoformat()
    if granularidade == "semana":
        ano, semana, _ = dia.isocalendar()
        return f"{ano}-S{semana:02d}"
    return dia.strftime("%Y-%m")


def _dia(momento: datetime) -> date:
    return momento.astimezone(FUSO).date()


# ---------- IND-01 Volume ----------

class PontoVolume(BaseModel):
    periodo: str
    abertos: int = 0
    solucionados: int = 0
    fechados: int = 0


class Volume(BaseModel):
    granularidade: Granularidade
    abertos: int
    solucionados: int
    fechados: int
    serie: list[PontoVolume]


def volume(chamados: list[Chamado], periodo: Periodo, granularidade: Granularidade = "dia") -> Volume:
    pontos: dict[str, PontoVolume] = {}
    dia = periodo.inicio
    while dia <= periodo.fim:  # pré-cria todos os buckets para a série não ter buracos
        chave = _chave_tempo(dia, granularidade)
        pontos.setdefault(chave, PontoVolume(periodo=chave))
        dia += timedelta(days=1)

    for c in chamados:
        for campo, momento in (("abertos", c.aberto_em), ("solucionados", c.solucionado_em), ("fechados", c.fechado_em)):
            if periodo.contem(momento):
                ponto = pontos[_chave_tempo(_dia(momento), granularidade)]
                setattr(ponto, campo, getattr(ponto, campo) + 1)

    serie = [pontos[k] for k in sorted(pontos)]
    return Volume(
        granularidade=granularidade,
        abertos=sum(p.abertos for p in serie),
        solucionados=sum(p.solucionados for p in serie),
        fechados=sum(p.fechados for p in serie),
        serie=serie,
    )


# ---------- IND-02 Backlog e aging ----------

class FaixaAging(BaseModel):
    faixa: str
    quantidade: int


class BacklogGrupo(BaseModel):
    grupo: str
    total: int
    faixas: list[FaixaAging]


class Backlog(BaseModel):
    total: int
    faixas: list[FaixaAging]
    por_grupo: list[BacklogGrupo]


def _faixa(idade_dias: int) -> str:
    for nome, minimo, maximo in FAIXAS_AGING:
        if idade_dias >= minimo and (maximo is None or idade_dias <= maximo):
            return nome
    return FAIXAS_AGING[0][0]  # idade negativa (relógio adiantado): trata como recém-aberto


def _contar_faixas(contador: Counter) -> list[FaixaAging]:
    return [FaixaAging(faixa=nome, quantidade=contador[nome]) for nome, _, _ in FAIXAS_AGING]


def backlog(chamados: list[Chamado], agora: datetime) -> Backlog:
    geral: Counter = Counter()
    por_grupo: dict[str, Counter] = defaultdict(Counter)
    for c in chamados:
        if not c.status.aberto or c.aberto_em > agora:
            continue
        faixa = _faixa((agora - c.aberto_em).days)
        geral[faixa] += 1
        for grupo in valores_dimensao(c, "grupo_tecnico"):
            por_grupo[grupo][faixa] += 1

    grupos = [
        BacklogGrupo(grupo=g, total=sum(cont.values()), faixas=_contar_faixas(cont)) for g, cont in por_grupo.items()
    ]
    grupos.sort(key=lambda g: (-g.total, g.grupo))
    return Backlog(total=sum(geral.values()), faixas=_contar_faixas(geral), por_grupo=grupos)


# ---------- IND-03 / IND-04 Cumprimento de SLA ----------

class ContagemSla(BaseModel):
    valor: str
    percentual: float | None
    cumpridos: int
    elegiveis: int


class Sla(BaseModel):
    tipo: TipoSla
    percentual: float | None
    cumpridos: int
    elegiveis: int
    dimensao: Dimensao | None
    por_dimensao: list[ContagemSla]
    serie_mensal: list[ContagemSla]


def _avaliar_sla(chamado: Chamado, tipo: TipoSla, periodo: Periodo) -> tuple[datetime, bool] | None:
    """Retorna (momento de referência, cumprido) se o chamado é elegível, senão None."""
    if tipo == "tto":
        prazo, momento = chamado.prazo_tto, chamado.assumido_em
    else:
        prazo, momento = chamado.prazo_ttr, chamado.solucionado_em
    if prazo is None or not periodo.contem(momento):
        return None
    return momento, momento <= prazo


def _consolidar(contagens: dict[str, list[int]]) -> list[ContagemSla]:
    return [
        ContagemSla(valor=valor, percentual=_pct(c, e), cumpridos=c, elegiveis=e)
        for valor, (c, e) in contagens.items()
    ]


def sla(chamados: list[Chamado], periodo: Periodo, tipo: TipoSla, dimensao: Dimensao | None = None) -> Sla:
    cumpridos = elegiveis = 0
    por_dimensao: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    por_mes: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for c in chamados:
        avaliacao = _avaliar_sla(c, tipo, periodo)
        if avaliacao is None:
            continue
        momento, ok = avaliacao
        elegiveis += 1
        cumpridos += ok
        mes = por_mes[_chave_tempo(_dia(momento), "mes")]
        mes[0] += ok
        mes[1] += 1
        if dimensao:
            for valor in valores_dimensao(c, dimensao):
                por_dimensao[valor][0] += ok
                por_dimensao[valor][1] += 1

    lista_dimensao = sorted(_consolidar(por_dimensao), key=lambda x: (-x.elegiveis, x.valor))
    serie = sorted(_consolidar(por_mes), key=lambda x: x.valor)
    return Sla(
        tipo=tipo,
        percentual=_pct(cumpridos, elegiveis),
        cumpridos=cumpridos,
        elegiveis=elegiveis,
        dimensao=dimensao,
        por_dimensao=lista_dimensao,
        serie_mensal=serie,
    )


# ---------- IND-05 SLA vencido ou em risco ----------

Situacao = Literal["vencido", "em_risco"]


class ChamadoEmRisco(BaseModel):
    id: int
    titulo: str
    grupos_tecnicos: list[str]
    prioridade: int
    prazo_ttr: datetime
    horas_restantes: float
    situacao: Situacao


class SlaEmRisco(BaseModel):
    vencidos: int
    em_risco: int
    itens: list[ChamadoEmRisco]


def sla_em_risco(chamados: list[Chamado], agora: datetime, limite: int = 50) -> SlaEmRisco:
    itens: list[ChamadoEmRisco] = []
    for c in chamados:
        if not c.status.aberto or c.prazo_ttr is None:
            continue
        restante = c.prazo_ttr - agora
        if restante < timedelta(0):
            situacao: Situacao = "vencido"
        elif restante < (c.prazo_ttr - c.aberto_em) * LIMIAR_RISCO:
            situacao = "em_risco"
        else:
            continue
        itens.append(
            ChamadoEmRisco(
                id=c.id,
                titulo=c.titulo,
                grupos_tecnicos=c.grupos_tecnicos,
                prioridade=c.prioridade,
                prazo_ttr=c.prazo_ttr,
                horas_restantes=_horas(restante.total_seconds()),
                situacao=situacao,
            )
        )
    itens.sort(key=lambda i: (i.prazo_ttr, i.id))
    return SlaEmRisco(
        vencidos=sum(i.situacao == "vencido" for i in itens),
        em_risco=sum(i.situacao == "em_risco" for i in itens),
        itens=itens[:limite],
    )


# ---------- IND-06 Tempos de atendimento e solução ----------

class Estatistica(BaseModel):
    quantidade: int
    media_horas: float | None
    mediana_horas: float | None
    p90_horas: float | None


class Tempos(BaseModel):
    atendimento: Estatistica
    solucao: Estatistica


def _estatistica(segundos: list[float]) -> Estatistica:
    if not segundos:
        return Estatistica(quantidade=0, media_horas=None, mediana_horas=None, p90_horas=None)
    ordenados = sorted(segundos)
    p90 = ordenados[math.ceil(0.9 * len(ordenados)) - 1]  # nearest-rank
    return Estatistica(
        quantidade=len(ordenados),
        media_horas=_horas(statistics.fmean(ordenados)),
        mediana_horas=_horas(statistics.median(ordenados)),
        p90_horas=_horas(p90),
    )


def tempos(chamados: list[Chamado], periodo: Periodo) -> Tempos:
    atendimento, solucao = [], []
    for c in chamados:
        if periodo.contem(c.assumido_em):
            atendimento.append(c.segundos_ate_assumir or (c.assumido_em - c.aberto_em).total_seconds())
        if periodo.contem(c.solucionado_em):
            solucao.append(c.segundos_ate_solucionar or (c.solucionado_em - c.aberto_em).total_seconds())
    return Tempos(atendimento=_estatistica(atendimento), solucao=_estatistica(solucao))


# ---------- IND-07 Distribuição por dimensão ----------

class ItemDistribuicao(BaseModel):
    valor: str
    quantidade: int


class Distribuicao(BaseModel):
    dimensao: Dimensao
    total_chamados: int
    itens: list[ItemDistribuicao]
    outros: int


def distribuicao(chamados: list[Chamado], periodo: Periodo, dimensao: Dimensao, top_n: int = 10) -> Distribuicao:
    no_periodo = [c for c in chamados if periodo.contem(c.aberto_em)]
    contagem: Counter = Counter(v for c in no_periodo for v in valores_dimensao(c, dimensao))
    ordenados = sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))
    topo = ordenados[:top_n]
    return Distribuicao(
        dimensao=dimensao,
        total_chamados=len(no_periodo),
        itens=[ItemDistribuicao(valor=v, quantidade=q) for v, q in topo],
        outros=sum(q for _, q in ordenados[top_n:]),
    )


# ---------- valores válidos para filtros ----------

class ValoresFiltro(BaseModel):
    grupos_tecnicos: list[str]
    categorias: list[str]
    entidades: list[str]
    prioridades: dict[int, str]
    tipos: list[str]


def _com_categorias_pai(categorias: set[str]) -> set[str]:
    # "Hardware > Notebook" também habilita filtrar por "Hardware" (inclui subcategorias)
    partes = (c.split(" > ") for c in categorias)
    return {" > ".join(p[: i + 1]) for p in partes for i in range(len(p))}


def valores_filtro(chamados: list[Chamado]) -> ValoresFiltro:
    return ValoresFiltro(
        grupos_tecnicos=sorted({g for c in chamados for g in c.grupos_tecnicos}),
        categorias=sorted(_com_categorias_pai({c.categoria for c in chamados if c.categoria})),
        entidades=sorted({c.entidade for c in chamados}),
        prioridades=NOMES_PRIORIDADE,
        tipos=["incidente", "requisicao"],
    )
