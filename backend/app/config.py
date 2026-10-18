from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR.parent / ".env", extra="ignore")

    glpi_adapter: Literal["mock", "rest"] = "mock"
    mock_data_path: Path = BACKEND_DIR / "data" / "mock" / "glpi_mock.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
