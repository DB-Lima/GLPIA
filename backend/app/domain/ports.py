from typing import Protocol

from app.domain.models import Chamado, FiltroChamados


class GlpiPort(Protocol):
    """Origem de chamados normalizados. Implementações ficam em app/adapters/glpi (ADR-0002)."""

    async def listar_chamados(self, filtro: FiltroChamados) -> list[Chamado]: ...
