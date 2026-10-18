"""Remove dados pessoais do texto do usuário antes de qualquer chamada a um LLM externo (ADR-0004)."""

import re

PADROES = [
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[e-mail removido]"),
    (re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)"), "[CPF removido]"),
]


def redigir(texto: str) -> tuple[str, int]:
    """Retorna o texto sem e-mails/CPFs e quantas substituições foram feitas."""
    total = 0
    for padrao, substituto in PADROES:
        texto, n = padrao.subn(substituto, texto)
        total += n
    return texto, total
