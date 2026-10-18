from datetime import date, datetime

import pytest

from app.domain.filtros import filtrar
from app.domain.models import FUSO, Chamado, FiltroChamados, StatusChamado


def _chamado(id_: int, aberto_em: datetime, **extra) -> Chamado:
    base = dict(
        id=id_,
        entidade="Raiz > Unidade Curitiba",
        titulo="Teste",
        aberto_em=aberto_em,
        assumido_em=None,
        solucionado_em=None,
        fechado_em=None,
        status=StatusChamado.NOVO,
        tipo="incidente",
        prioridade=3,
        categoria="Acesso > Senha",
        grupos_tecnicos=["N1 - Service Desk"],
        prazo_tto=None,
        prazo_ttr=None,
        segundos_ate_assumir=None,
        segundos_ate_solucionar=None,
        excluido=False,
    )
    return Chamado(**(base | extra))


CHAMADOS = [
    _chamado(1, datetime(2026, 8, 31, 23, 59, tzinfo=FUSO)),
    _chamado(2, datetime(2026, 9, 1, 0, 0, tzinfo=FUSO)),
    _chamado(3, datetime(2026, 9, 30, 23, 59, tzinfo=FUSO), grupos_tecnicos=["N2 - Suporte Técnico"]),
    _chamado(4, datetime(2026, 10, 1, 0, 0, tzinfo=FUSO), categoria="Acesso"),
    _chamado(5, datetime(2026, 9, 15, 10, 0, tzinfo=FUSO), excluido=True),
    _chamado(6, datetime(2026, 9, 15, 10, 0, tzinfo=FUSO), categoria="Acessorios", tipo="requisicao"),
]


def _ids(filtro: FiltroChamados) -> list[int]:
    return [c.id for c in filtrar(CHAMADOS, filtro)]


def test_periodo_inclui_os_dois_extremos():
    filtro = FiltroChamados(periodo_inicio=date(2026, 9, 1), periodo_fim=date(2026, 9, 30))
    assert _ids(filtro) == [2, 3, 6]


def test_periodo_usa_fuso_de_sao_paulo():
    # 2026-09-01 02:30 UTC ainda é 31/08 em São Paulo
    utc = datetime.fromisoformat("2026-09-01T02:30:00+00:00")
    chamado = _chamado(9, utc)
    assert filtrar([chamado], FiltroChamados(periodo_inicio=date(2026, 9, 1))) == []


def test_excluidos_ficam_fora_por_padrao():
    assert 5 not in _ids(FiltroChamados())
    assert 5 in _ids(FiltroChamados(incluir_excluidos=True))


def test_categoria_inclui_subcategorias_sem_confundir_prefixo():
    assert _ids(FiltroChamados(categoria="Acesso")) == [1, 2, 3, 4]
    assert _ids(FiltroChamados(categoria="Acesso", incluir_subcategorias=False)) == [4]


def test_grupo_e_tipo():
    assert _ids(FiltroChamados(grupo_tecnico="N2 - Suporte Técnico")) == [3]
    assert _ids(FiltroChamados(tipo="requisicao")) == [6]


def test_periodo_invertido_e_invalido():
    with pytest.raises(ValueError):
        FiltroChamados(periodo_inicio=date(2026, 9, 30), periodo_fim=date(2026, 9, 1))
