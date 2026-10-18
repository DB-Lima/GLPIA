from datetime import datetime

from app.domain.models import FUSO, Chamado, StatusChamado


def dt(texto: str) -> datetime:
    """'2026-10-01 09:00' no fuso de São Paulo."""
    return datetime.strptime(texto, "%Y-%m-%d %H:%M").replace(tzinfo=FUSO)


def chamado(id_: int, aberto_em: datetime, **extra) -> Chamado:
    base = dict(
        id=id_,
        entidade="Raiz > Unidade Curitiba",
        titulo=f"Chamado {id_}",
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
