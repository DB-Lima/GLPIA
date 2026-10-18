import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.adapters.glpi.mock import MockGlpiAdapter, converter
from app.domain.models import FiltroChamados, StatusChamado
from tests.conftest import BACKEND_DIR, MOCK_PATH

SCRIPT = BACKEND_DIR / "scripts" / "gerar_mock.py"


def _gerar(saida: Path, *args: str) -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--saida", str(saida), *args], check=True, capture_output=True)


def test_gerador_e_deterministico(tmp_path):
    _gerar(tmp_path / "a.json")
    _gerar(tmp_path / "b.json")
    assert (tmp_path / "a.json").read_bytes() == (tmp_path / "b.json").read_bytes()


def test_seed_diferente_gera_dados_diferentes(tmp_path):
    _gerar(tmp_path / "a.json", "--quantidade", "200")
    _gerar(tmp_path / "b.json", "--quantidade", "200", "--seed", "7")
    assert (tmp_path / "a.json").read_bytes() != (tmp_path / "b.json").read_bytes()


def test_dataset_versionado_esta_atualizado(tmp_path, dados_mock):
    _gerar(tmp_path / "novo.json")
    assert json.loads((tmp_path / "novo.json").read_text(encoding="utf-8")) == dados_mock


def test_dataset_tem_cerca_de_5000_chamados(dados_mock):
    assert len(dados_mock["tickets"]) == 5000


def test_dataset_cobre_casos_de_borda(dados_mock):
    tickets = dados_mock["tickets"]
    com_grupo = {v["tickets_id"] for v in dados_mock["groups_tickets"] if v["type"] == 2}
    assert any(t["time_to_resolve"] is None for t in tickets), "SLA nulo"
    assert any(t["id"] not in com_grupo for t in tickets), "sem grupo técnico"
    assert any(t["status"] == 4 for t in tickets), "pendente"
    assert any(t["is_deleted"] == 1 for t in tickets), "excluído"
    assert any(
        t["solvedate"] and t["time_to_resolve"] and t["solvedate"] > t["time_to_resolve"] for t in tickets
    ), "solucionado após o prazo"


def test_dataset_nao_tem_dados_pessoais(dados_mock):
    bruto = MOCK_PATH.read_text(encoding="utf-8")
    assert "@" not in bruto
    for tabela in ("users", "tickets_users"):
        assert tabela not in dados_mock
    proibidos = {"users_id_recipient", "users_id_lastupdater", "content"}
    assert not proibidos & set(dados_mock["tickets"][0])


def test_conversao_para_modelo_normalizado(dados_mock):
    chamados = converter(dados_mock)
    assert len(chamados) == len(dados_mock["tickets"])
    bruto = dados_mock["tickets"][0]
    chamado = chamados[0]
    assert chamado.id == bruto["id"]
    assert chamado.aberto_em.strftime("%Y-%m-%d %H:%M:%S") == bruto["date"]
    assert chamado.aberto_em.utcoffset() is not None
    assert chamado.status == StatusChamado(bruto["status"])
    # grupo requerente (type 1) não entra como grupo técnico
    assert all("Solicitantes" not in g for c in chamados for g in c.grupos_tecnicos)


async def test_adapter_filtra_excluidos_e_periodo():
    adapter = MockGlpiAdapter(MOCK_PATH)
    todos = await adapter.listar_chamados(FiltroChamados(incluir_excluidos=True))
    sem_excluidos = await adapter.listar_chamados(FiltroChamados())
    assert len(todos) == 5000
    assert len(sem_excluidos) == len([c for c in todos if not c.excluido])

    setembro = await adapter.listar_chamados(FiltroChamados(periodo_inicio="2026-09-01", periodo_fim="2026-09-30"))
    assert setembro and all(c.aberto_em.month == 9 for c in setembro)


async def test_adapter_avisa_quando_dataset_nao_existe(tmp_path):
    adapter = MockGlpiAdapter(tmp_path / "nao_existe.json")
    with pytest.raises(FileNotFoundError, match="gerar_mock.py"):
        await adapter.listar_chamados(FiltroChamados())


def test_dominio_nao_importa_adapters():
    for arquivo in (BACKEND_DIR / "app" / "domain").glob("*.py"):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for no in ast.walk(arvore):
            modulos = []
            if isinstance(no, ast.Import):
                modulos = [alias.name for alias in no.names]
            elif isinstance(no, ast.ImportFrom) and no.module:
                modulos = [no.module]
            assert not any(m.startswith("app.adapters") for m in modulos), f"{arquivo.name} importa adapter"
