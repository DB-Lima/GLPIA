"""Gera um dataset FICTÍCIO de chamados no formato das tabelas do GLPI.

Determinístico: mesma seed e mesma quantidade produzem o mesmo arquivo, byte a byte.
Não contém nomes nem e-mails de pessoas; títulos vêm de modelos fixos.

Uso: python scripts/gerar_mock.py [--seed 42] [--quantidade 5000] [--saida caminho.json]
"""

import argparse
import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

REFERENCIA = datetime(2026, 10, 15, 18, 0, 0)  # "agora" do dataset, fixo para garantir determinismo
JANELA_DIAS = 180
FORMATO = "%Y-%m-%d %H:%M:%S"
SAIDA_PADRAO = Path(__file__).resolve().parent.parent / "data" / "mock" / "glpi_mock.json"

ENTIDADES = [
    (0, "Raiz", 0.05),
    (1, "Raiz > Unidade Curitiba", 0.50),
    (2, "Raiz > Unidade São Paulo", 0.30),
    (3, "Raiz > Unidade Manaus", 0.15),
]

GRUPOS = {
    1: "N1 - Service Desk",
    2: "N2 - Suporte Técnico",
    3: "N3 - Infraestrutura",
    4: "N3 - Sistemas",
    5: "Redes",
    6: "Telefonia",
    7: "Solicitantes - Comercial",  # usado só como grupo requerente (type 1)
}
GRUPO_N2 = 2
GRUPO_REQUERENTE = 7

# id, nome completo, grupo técnico principal, peso, títulos
CATEGORIAS = [
    (1, "Acesso", 1, 0.00, []),
    (2, "Acesso > Senha", 1, 0.18, ["Redefinição de senha de rede", "Conta bloqueada após tentativas", "Senha expirada no sistema"]),
    (3, "Acesso > VPN", 5, 0.08, ["Falha ao conectar na VPN", "VPN desconecta com frequência", "Solicitação de acesso VPN"]),
    (4, "Hardware", 2, 0.00, []),
    (5, "Hardware > Notebook", 2, 0.12, ["Notebook não liga", "Tela do notebook com defeito", "Troca de bateria do notebook"]),
    (6, "Hardware > Impressora", 2, 0.08, ["Impressora não imprime", "Atolamento de papel recorrente", "Instalar impressora de rede"]),
    (7, "Software", 1, 0.00, []),
    (8, "Software > Instalação", 1, 0.14, ["Instalar pacote de escritório", "Instalar ferramenta de desenvolvimento", "Atualização de software solicitada"]),
    (9, "Software > ERP", 4, 0.12, ["Erro ao emitir relatório no ERP", "Lentidão no módulo financeiro", "Permissão de acesso a tela do ERP"]),
    (10, "Rede > Wi-Fi", 5, 0.08, ["Wi-Fi instável na sala de reunião", "Sem sinal de Wi-Fi no andar", "Acesso Wi-Fi para visitante"]),
    (11, "Infraestrutura > Servidor", 3, 0.06, ["Servidor de arquivos indisponível", "Espaço em disco esgotado no servidor", "Solicitação de nova VM"]),
    (12, "Telefonia > Ramal", 6, 0.06, ["Ramal sem tom de discagem", "Configurar novo ramal", "Transferência de ramal"]),
]

PRIORIDADES = [(1, 0.05), (2, 0.15), (3, 0.50), (4, 0.20), (5, 0.08), (6, 0.02)]
SLA_TTO_HORAS = {1: 8, 2: 8, 3: 4, 4: 2, 5: 1, 6: 0.5}
SLA_TTR_HORAS = {1: 72, 2: 48, 3: 24, 4: 16, 5: 8, 6: 4}
DIAS_ATE_FECHAR = 3


def _escolher(rng: random.Random, pares):
    itens, pesos = zip(*pares)
    return rng.choices(itens, weights=pesos, k=1)[0]


def _fmt(valor: datetime | None) -> str | None:
    return valor.strftime(FORMATO) if valor else None


def _data_abertura(rng: random.Random) -> datetime:
    while True:
        dia = REFERENCIA.date() - timedelta(days=rng.randrange(JANELA_DIAS))
        if dia.weekday() >= 5 and rng.random() < 0.7:
            continue  # menos chamados no fim de semana
        momento = datetime(dia.year, dia.month, dia.day, rng.randint(8, 17), rng.randrange(60), rng.randrange(60))
        if momento <= REFERENCIA:
            return momento


def _duracao(rng: random.Random, prazo_horas: float, fator_mediana: float, sigma: float) -> timedelta:
    horas = rng.lognormvariate(math.log(prazo_horas * fator_mediana), sigma)
    return timedelta(seconds=int(horas * 3600))


def _gerar_chamado(rng: random.Random) -> tuple[dict, list[tuple[int, int]]]:
    aberto = _data_abertura(rng)
    categoria = _escolher(rng, [(c, c[3]) for c in CATEGORIAS if c[3] > 0])
    cat_id, _, grupo_principal, _, titulos = categoria
    prioridade = _escolher(rng, PRIORIDADES)
    tem_sla = rng.random() >= 0.10
    # Chamado que fica aberto além do previsto: mais comum entre os recentes, gera backlog com aging.
    dias = (REFERENCIA - aberto).days
    parado = rng.random() < 0.01 + 0.30 * math.exp(-dias / 15)

    tto = timedelta(hours=SLA_TTO_HORAS[prioridade])
    ttr = timedelta(hours=SLA_TTR_HORAS[prioridade])
    assumido = aberto + _duracao(rng, SLA_TTO_HORAS[prioridade], 0.5, 0.9)
    solucionado = aberto + _duracao(rng, SLA_TTR_HORAS[prioridade], 0.45, 1.0)
    solucionado = max(solucionado, assumido + timedelta(minutes=5))

    fechado = None
    espera = 0
    if assumido > REFERENCIA:
        assumido = solucionado = None
        status = 1
    elif solucionado > REFERENCIA or parado:
        solucionado = None
        status = _escolher(rng, [(2, 0.60), (3, 0.15), (4, 0.25)])
        if status == 4:
            espera = rng.randint(1, 72) * 3600
    else:
        candidato = solucionado + timedelta(days=DIAS_ATE_FECHAR)
        if candidato <= REFERENCIA:
            fechado, status = candidato, 6
        else:
            status = 5

    chamado = {
        "entities_id": _escolher(rng, [(e[0], e[2]) for e in ENTIDADES]),
        "name": rng.choice(titulos),
        "date": _fmt(aberto),
        "takeintoaccountdate": _fmt(assumido),
        "solvedate": _fmt(solucionado),
        "closedate": _fmt(fechado),
        "status": status,
        "type": 1 if rng.random() < 0.6 else 2,
        "priority": prioridade,
        "urgency": min(prioridade, 5),
        "impact": rng.randint(1, 5),
        "itilcategories_id": cat_id,
        "time_to_own": _fmt(aberto + tto) if tem_sla else None,
        "time_to_resolve": _fmt(aberto + ttr) if tem_sla else None,
        "slas_id_tto": prioridade if tem_sla else 0,
        "slas_id_ttr": 10 + prioridade if tem_sla else 0,
        "takeintoaccount_delay_stat": int((assumido - aberto).total_seconds()) if assumido else 0,
        "solve_delay_stat": int((solucionado - aberto).total_seconds()) if solucionado else 0,
        "waiting_duration": espera,
        "is_deleted": 1 if rng.random() < 0.02 else 0,
    }

    vinculos: list[tuple[int, int]] = []  # (groups_id, type)
    if rng.random() >= 0.05:  # ~5% sem grupo técnico atribuído
        vinculos.append((grupo_principal, 2))
        if grupo_principal != GRUPO_N2 and rng.random() < 0.15:
            vinculos.append((GRUPO_N2, 2))
    if rng.random() < 0.10:
        vinculos.append((GRUPO_REQUERENTE, 1))
    return chamado, vinculos


def gerar(seed: int, quantidade: int) -> dict:
    rng = random.Random(seed)
    gerados = [_gerar_chamado(rng) for _ in range(quantidade)]
    gerados.sort(key=lambda par: par[0]["date"])

    tickets, groups_tickets = [], []
    for indice, (chamado, vinculos) in enumerate(gerados):
        ticket_id = 10001 + indice
        tickets.append({"id": ticket_id, **chamado})
        for groups_id, tipo in vinculos:
            groups_tickets.append(
                {"id": len(groups_tickets) + 1, "tickets_id": ticket_id, "groups_id": groups_id, "type": tipo}
            )

    return {
        "meta": {
            "aviso": "Dados fictícios gerados por backend/scripts/gerar_mock.py",
            "seed": seed,
            "quantidade": quantidade,
            "referencia": _fmt(REFERENCIA),
        },
        "entities": [{"id": i, "completename": nome} for i, nome, _ in ENTIDADES],
        "groups": [{"id": i, "completename": nome} for i, nome in GRUPOS.items()],
        "itilcategories": [{"id": c[0], "completename": c[1]} for c in CATEGORIAS],
        "tickets": tickets,
        "groups_tickets": groups_tickets,
    }


def serializar(dados: dict) -> str:
    """JSON com um registro por linha: diffs legíveis e saída estável."""
    partes = []
    for chave, valor in dados.items():
        if isinstance(valor, list):
            linhas = ",\n".join("    " + json.dumps(item, ensure_ascii=False) for item in valor)
            partes.append(f'  "{chave}": [\n{linhas}\n  ]')
        else:
            partes.append(f'  "{chave}": {json.dumps(valor, ensure_ascii=False)}')
    return "{\n" + ",\n".join(partes) + "\n}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quantidade", type=int, default=5000)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(serializar(gerar(args.seed, args.quantidade)))
    print(f"{args.quantidade} chamados gravados em {args.saida}")


if __name__ == "__main__":
    main()
