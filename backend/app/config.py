from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR.parent / ".env"

# Exporta o .env para o ambiente: o LiteLLM lê as chaves dos provedores (ex.: ANTHROPIC_API_KEY) de os.environ.
load_dotenv(ENV_FILE, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    glpi_adapter: Literal["mock", "rest"] = "mock"
    mock_data_path: Path = BACKEND_DIR / "data" / "mock" / "glpi_mock.json"

    llm_model: str = "anthropic/claude-opus-5-5"
    llm_fallback_model: str | None = None
    llm_timeout_segundos: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
