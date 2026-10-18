from datetime import date, datetime


def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_amostra_respeita_limite_e_retorna_filtro(client):
    resposta = client.get("/api/v1/chamados/amostra", params={"limite": 5})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo["itens"]) == 5
    assert corpo["total"] > 5
    assert "filtro_aplicado" in corpo
    datas = [item["aberto_em"] for item in corpo["itens"]]
    assert datas == sorted(datas, reverse=True)


def test_amostra_filtra_por_periodo(client):
    params = {"periodo_inicio": "2026-09-01", "periodo_fim": "2026-09-30", "limite": 100}
    corpo = client.get("/api/v1/chamados/amostra", params=params).json()
    assert corpo["total"] > 0
    assert corpo["filtro_aplicado"]["periodo_inicio"] == "2026-09-01"
    for item in corpo["itens"]:
        assert date(2026, 9, 1) <= datetime.fromisoformat(item["aberto_em"]).date() <= date(2026, 9, 30)


def test_amostra_rejeita_periodo_invertido(client):
    params = {"periodo_inicio": "2026-09-30", "periodo_fim": "2026-09-01"}
    assert client.get("/api/v1/chamados/amostra", params=params).status_code == 422


def test_amostra_rejeita_limite_fora_da_faixa(client):
    assert client.get("/api/v1/chamados/amostra", params={"limite": 0}).status_code == 422
    assert client.get("/api/v1/chamados/amostra", params={"limite": 101}).status_code == 422
