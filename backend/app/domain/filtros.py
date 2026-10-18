from collections.abc import Iterable

from app.domain.models import FUSO, Chamado, FiltroChamados


def _categoria_confere(categoria: str | None, filtro: FiltroChamados) -> bool:
    if categoria is None:
        return False
    if categoria == filtro.categoria:
        return True
    return filtro.incluir_subcategorias and categoria.startswith(f"{filtro.categoria} > ")


def atende_filtro(chamado: Chamado, filtro: FiltroChamados) -> bool:
    if chamado.excluido and not filtro.incluir_excluidos:
        return False
    dia_abertura = chamado.aberto_em.astimezone(FUSO).date()
    if filtro.periodo_inicio and dia_abertura < filtro.periodo_inicio:
        return False
    if filtro.periodo_fim and dia_abertura > filtro.periodo_fim:
        return False
    if filtro.grupo_tecnico and filtro.grupo_tecnico not in chamado.grupos_tecnicos:
        return False
    if filtro.categoria and not _categoria_confere(chamado.categoria, filtro):
        return False
    if filtro.prioridade and chamado.prioridade != filtro.prioridade:
        return False
    if filtro.tipo and chamado.tipo != filtro.tipo:
        return False
    if filtro.entidade and chamado.entidade != filtro.entidade:
        return False
    return True


def filtrar(chamados: Iterable[Chamado], filtro: FiltroChamados) -> list[Chamado]:
    return [c for c in chamados if atende_filtro(c, filtro)]
