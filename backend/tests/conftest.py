import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parent.parent
MOCK_PATH = BACKEND_DIR / "data" / "mock" / "glpi_mock.json"


@pytest.fixture(scope="session")
def dados_mock() -> dict:
    return json.loads(MOCK_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def client() -> TestClient:
    app = create_app(Settings(glpi_adapter="mock", mock_data_path=MOCK_PATH))
    with TestClient(app) as cliente:
        yield cliente
