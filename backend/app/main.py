from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.glpi import criar_adapter
from app.ai.agente import Agente
from app.ai.llm import ClienteLiteLLM
from app.api.v1.chamados import router as chamados_router
from app.api.v1.chat import router as chat_router
from app.api.v1.indicadores import filtros_router
from app.api.v1.indicadores import router as indicadores_router
from app.config import Settings, get_settings
from app.services.consultas import ServicoIndicadores


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.glpi = criar_adapter(settings)
        app.state.servico = ServicoIndicadores(app.state.glpi)
        app.state.agente = Agente(
            app.state.servico,
            ClienteLiteLLM(settings.llm_timeout_segundos),
            [settings.llm_model, settings.llm_fallback_model],
        )
        yield

    app = FastAPI(title="GLPIA API", version="0.1.0", lifespan=lifespan)

    @app.get("/health", tags=["infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (chamados_router, indicadores_router, filtros_router, chat_router):
        app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
