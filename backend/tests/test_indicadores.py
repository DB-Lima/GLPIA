"""Valores esperados calculados à mão a partir de docs/01-indicadores.md."""

from datetime import date

import pytest

from app.domain import indicadores as ind
from app.domain.filtros import filtrar
from app.domain.models import FiltroChamados, StatusChamado
from app.services.consultas import ServicoIndicadores
from tests.fabrica import chamado, dt

N1, N2 = "N1 - Service Desk", "N2 - Suporte Técnico"
AGORA = dt("2026-10-15 18:00")
OUTUBRO = ind.Periodo(inicio=date(2026, 10, 1), fim=date(2026, 10, 15))

C1 = chamado(  # assumido e solucionado no prazo (solução exatamente no limite)
    1, dt("2026-10-01 09:00"),
    assumido_em=dt("2026-10-01 10:00"), prazo_tto=dt("2026-10-01 11:00"),
    solucionado_em=dt("2026-10-02 09:00"), prazo_ttr=dt("2026-10-02 09:00"),
    fechado_em=dt("2026-10-05 09:00"), status=StatusChamado.FECHADO,
    segundos_ate_assumir=3600, segundos_ate_solucionar=86400,
)
C2 = chamado(  # estourou TTO e TTR; sem *_delay_stat (usa diferença de datas); dois grupos
    2, dt("2026-10-03 08:00"),
    assumido_em=dt("2026-10-03 14:00"), prazo_tto=dt("2026-10-03 12:00"),
    solucionado_em=dt("2026-10-06 08:00"), prazo_ttr=dt("2026-10-04 08:00"),
    status=StatusChamado.SOLUCIONADO, grupos_tecnicos=[N1, N2],
    categoria="Hardware > Notebook", prioridade=4,
)
C3 = chamado(  # aberto e assumido antes do período, solucionado (atrasado) dentro dele
    3, dt("2026-09-28 10:00"),
    assumido_em=dt("2026-09-28 11:00"), prazo_tto=dt("2026-09-28 12:00"),
    solucionado_em=dt("2026-10-02 10:00"), prazo_ttr=dt("2026-09-29 10:00"),
    fechado_em=dt("2026-10-05 10:00"), status=StatusChamado.FECHADO,
    grupos_tecnicos=[N2], categoria="Acesso > VPN",
    segundos_ate_assumir=3600, segundos_ate_solucionar=345600,
)
C4 = chamado(  # aberto, faltam 2 h de 12 h de prazo -> em risco
    4, dt("2026-10-15 08:00"),
    assumido_em=dt("2026-10-15 09:00"), prazo_tto=dt("2026-10-15 10:00"),
    prazo_ttr=dt("2026-10-15 20:00"), status=StatusChamado.EM_ATENDIMENTO_ATRIBUIDO,
    grupos_tecnicos=[N2], prioridade=5, segundos_ate_assumir=3600,
)
C5 = chamado(  # novo, nunca assumido, sem grupo e sem categoria, SLA vencido
    5, dt("2026-10-01 12:00"),
    prazo_tto=dt("2026-10-01 16:00"), prazo_ttr=dt("2026-10-02 12:00"),
    grupos_tecnicos=[], categoria=None,
)
C6 = chamado(  # pendente antigo, sem SLA
    6, dt("2026-09-10 09:00"),
    assumido_em=dt("2026-09-10 10:00"), status=StatusChamado.PENDENTE,
    categoria="Hardware > Impressora", prioridade=2,
)
CHAMADOS = [C1, C2, C3, C4, C5, C6]


def test_volume_por_dia():
    r = ind.volume(CHAMADOS, OUTUBRO, "dia")
    assert (r.abertos, r.solucionados, r.fechados) == (4, 3, 2)
    assert len(r.serie) == 15  # um ponto por dia, inclusive os vazios
    pontos = {p.periodo: p for p in r.serie}
    assert pontos["2026-10-01"].abertos == 2
    assert pontos["2026-10-02"].solucionados == 2
    assert pontos["2026-10-05"].fechados == 2


def test_volume_por_mes_e_semana():
    assert [p.periodo for p in ind.volume(CHAMADOS, OUTUBRO, "mes").serie] == ["2026-10"]
    semanas = [p.periodo for p in ind.volume(CHAMADOS, OUTUBRO, "semana").serie]
    assert semanas == ["2026-S40", "2026-S41", "2026-S42"]


def test_backlog_e_aging():
    r = ind.backlog(CHAMADOS, AGORA)
    assert r.total == 3
    assert {f.faixa: f.quantidade for f in r.faixas} == {"0-2 d": 1, "3-7 d": 0, "8-15 d": 1, "16-30 d": 0, "> 30 d": 1}
    assert [(g.grupo, g.total) for g in r.por_grupo] == [(N1, 1), (N2, 1), (ind.SEM_GRUPO, 1)]


def test_sla_tto():
    r = ind.sla(CHAMADOS, OUTUBRO, "tto")
    # elegíveis: C1 (ok), C2 (atrasado), C4 (ok). C3 foi assumido fora do período; C5 nunca foi assumido; C6 sem prazo.
    assert (r.cumpridos, r.elegiveis, r.percentual) == (2, 3, 66.7)


def test_sla_ttr_por_grupo_e_mes():
    r = ind.sla(CHAMADOS, OUTUBRO, "ttr", dimensao="grupo_tecnico")
    assert (r.cumpridos, r.elegiveis, r.percentual) == (1, 3, 33.3)
    assert [(d.valor, d.cumpridos, d.elegiveis, d.percentual) for d in r.por_dimensao] == [
        (N1, 1, 2, 50.0),
        (N2, 0, 2, 0.0),
    ]
    assert [(m.valor, m.cumpridos, m.elegiveis) for m in r.serie_mensal] == [("2026-10", 1, 3)]


def test_sla_ignora_chamados_sem_prazo_no_denominador():
    sem_prazo = C1.model_copy(update={"id": 99, "prazo_tto": None, "prazo_ttr": None})
    assert ind.sla([sem_prazo], OUTUBRO, "tto").elegiveis == 0
    assert ind.sla([sem_prazo], OUTUBRO, "ttr").percentual is None
    assert ind.sla(CHAMADOS + [sem_prazo], OUTUBRO, "ttr").elegiveis == 3


def test_sla_em_risco():
    r = ind.sla_em_risco(CHAMADOS, AGORA)
    assert (r.vencidos, r.em_risco) == (1, 1)
    assert [(i.id, i.situacao, i.horas_restantes) for i in r.itens] == [(5, "vencido", -318.0), (4, "em_risco", 2.0)]
    assert len(ind.sla_em_risco(CHAMADOS, AGORA, limite=1).itens) == 1


def test_tempos():
    r = ind.tempos(CHAMADOS, OUTUBRO)
    # atendimento: C1 1 h, C2 6 h (diferença de datas), C4 1 h
    assert r.atendimento.model_dump() == {"quantidade": 3, "media_horas": 2.7, "mediana_horas": 1.0, "p90_horas": 6.0}
    # solução: C1 24 h, C2 72 h (diferença de datas), C3 96 h
    assert r.solucao.model_dump() == {"quantidade": 3, "media_horas": 64.0, "mediana_horas": 72.0, "p90_horas": 96.0}


def test_tempos_sem_dados():
    vazio = ind.tempos([], OUTUBRO)
    assert vazio.atendimento.quantidade == 0 and vazio.atendimento.media_horas is None


def test_distribuicao():
    r = ind.distribuicao(CHAMADOS, OUTUBRO, "categoria", top_n=2)
    assert r.total_chamados == 4
    assert [(i.valor, i.quantidade) for i in r.itens] == [("Acesso > Senha", 2), ("Hardware > Notebook", 1)]
    assert r.outros == 1

    grupos = ind.distribuicao(CHAMADOS, OUTUBRO, "grupo_tecnico")
    assert [(i.valor, i.quantidade) for i in grupos.itens] == [(N1, 2), (N2, 2), (ind.SEM_GRUPO, 1)]

    prioridades = ind.distribuicao(CHAMADOS, OUTUBRO, "prioridade")
    assert prioridades.itens[0].valor == "3 - Média"


def test_valores_filtro_inclui_categorias_pai():
    v = ind.valores_filtro(CHAMADOS)
    assert "Hardware" in v.categorias and "Hardware > Notebook" in v.categorias
    assert v.grupos_tecnicos == [N1, N2]


class PortaFalsa:
    def __init__(self, chamados):
        self.chamados = chamados
        self.chamadas = 0

    async def listar_chamados(self, filtro):
        self.chamadas += 1
        return filtrar(self.chamados, filtro)

    def agora(self):
        return AGORA


EXCLUIDO = chamado(  # cairia em todos os indicadores se não fosse excluído
    7, dt("2026-10-02 08:00"),
    assumido_em=dt("2026-10-02 09:00"), prazo_tto=dt("2026-10-02 10:00"),
    solucionado_em=dt("2026-10-02 12:00"), prazo_ttr=dt("2026-10-02 18:00"),
    fechado_em=dt("2026-10-03 08:00"), status=StatusChamado.FECHADO,
    excluido=True,
)
EXCLUIDO_ABERTO = chamado(8, dt("2026-10-01 08:00"), prazo_ttr=dt("2026-10-01 10:00"), excluido=True)


@pytest.mark.parametrize(
    "consulta",
    [
        lambda s, f: s.volume(f),
        lambda s, f: s.backlog(f),
        lambda s, f: s.sla(f, "tto"),
        lambda s, f: s.sla(f, "ttr"),
        lambda s, f: s.sla_em_risco(f),
        lambda s, f: s.tempos(f),
        lambda s, f: s.distribuicao(f, "categoria"),
    ],
    ids=["volume", "backlog", "sla_tto", "sla_ttr", "sla_em_risco", "tempos", "distribuicao"],
)
async def test_excluidos_nao_entram_em_nenhum_indicador(consulta):
    filtro = FiltroChamados(periodo_inicio=date(2026, 10, 1), periodo_fim=date(2026, 10, 15))
    sem = await consulta(ServicoIndicadores(PortaFalsa(CHAMADOS)), filtro)
    com = await consulta(ServicoIndicadores(PortaFalsa(CHAMADOS + [EXCLUIDO, EXCLUIDO_ABERTO])), filtro)
    assert com.resultado == sem.resultado


async def test_periodo_padrao_e_ultimos_30_dias_ate_a_referencia():
    resposta = await ServicoIndicadores(PortaFalsa(CHAMADOS)).volume(FiltroChamados())
    assert resposta.filtro_aplicado.periodo_inicio == date(2026, 9, 16)
    assert resposta.filtro_aplicado.periodo_fim == date(2026, 10, 15)
    assert resposta.referencia == AGORA


async def test_cache_evita_nova_leitura_para_o_mesmo_filtro():
    porta = PortaFalsa(CHAMADOS)
    servico = ServicoIndicadores(porta)
    primeira = await servico.sla(FiltroChamados(), "ttr")
    segunda = await servico.sla(FiltroChamados(), "ttr")
    assert primeira is segunda and porta.chamadas == 1
    await servico.sla(FiltroChamados(), "tto")
    assert porta.chamadas == 2


async def test_periodo_so_com_inicio_no_futuro_e_invalido():
    with pytest.raises(ValueError):
        await ServicoIndicadores(PortaFalsa(CHAMADOS)).volume(FiltroChamados(periodo_inicio=date(2027, 1, 1)))
