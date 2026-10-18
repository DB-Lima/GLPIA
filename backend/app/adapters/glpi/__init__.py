from app.adapters.glpi.mock import MockGlpiAdapter
from app.config import Settings
from app.domain.ports import GlpiPort


def criar_adapter(settings: Settings) -> GlpiPort:
    if settings.glpi_adapter == "mock":
        return MockGlpiAdapter(settings.mock_data_path)
    raise NotImplementedError("Adapter REST do GLPI ainda não implementado (SPEC-2026-0006)")
