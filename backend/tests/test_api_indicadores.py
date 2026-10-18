import time

import pytest

ENDPOINTS = ["volume", "backlog", "sla_tto", "sla_ttr", "sla_em_risco", "tempos", "distribuicao"]


@pytest.mark.parametrize("nome", ENDPOINTS)
def test_endpoint_responde_com_filtro_aplicado(client, nome):
    resposta = client.get(f"/api/v1/indicadores/{nome}", params={"grupo_tecnico": "N1 - Service Desk"})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["filtro_aplicado"]["grupo_tecnico"] == "N1 - Service Desk"
    assert corpo["filtro_aplicado"]["periodo_inicio"] and corpo["filtro_aplicado"]["periodo_fim"]
    assert corpo["resultado"]


def test_todos_os_indicadores_estao_documentados_no_swagger(client):
    caminhos = client.get("/openapi.json").json()["paths"]
    for nome in ENDPOINTS:
        assert f"/api/v1/indicadores/{nome}" in caminhos
    assert client.get("/docs").status_code == 200


def test_parametros_invalidos_retornam_422(client):
    assert client.get("/api/v1/indicadores/distribuicao", params={"dimensao": "cor"}).status_code == 422
    assert client.get("/api/v1/indicadores/volume", params={"granularidade": "ano"}).status_code == 422
    assert client.get("/api/v1/indicadores/volume", params={"periodo_inicio": "2030-01-01"}).status_code == 422


def test_valores_de_filtro(client):
    valores = client.get("/api/v1/filtros/valores").json()
    assert "N2 - Suporte Técnico" in valores["grupos_tecnicos"]
    assert "Hardware" in valores["categorias"]


@pytest.mark.parametrize("nome", ENDPOINTS)
def test_p95_abaixo_de_500ms_com_dataset_mock(client, nome):
    servico = client.app.state.servico
    client.get(f"/api/v1/indicadores/{nome}")  # aquece a leitura do JSON
    duracoes = []
    for _ in range(20):
        servico.cache.limpar()  # mede o cálculo, não o cache
        inicio = time.perf_counter()
        assert client.get(f"/api/v1/indicadores/{nome}").status_code == 200
        duracoes.append(time.perf_counter() - inicio)
    p95 = sorted(duracoes)[int(0.95 * len(duracoes)) - 1]
    assert p95 < 0.5, f"p95 de {nome} = {p95:.3f}s"
