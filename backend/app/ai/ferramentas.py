"""Ferramentas somente leitura expostas ao LLM (ADR-0003) e montagem das visualizações.

O LLM recebe apenas agregados e IDs (ADR-0004). Os gráficos devolvidos ao frontend são montados
aqui, a partir do resultado real da ferramenta, para que nenhum número venha do texto do modelo.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain import indicadores as ind
from app.domain.models import FiltroChamados, TipoChamado
from app.services.consultas import RespostaIndicador, ServicoIndicadores

CAMPOS_PROIBIDOS_LLM = {"titulo"}  # texto livre de chamado nunca vai ao LLM


# ---------- argumentos ----------

class ArgsFiltro(BaseModel):
    model_config = ConfigDict(extra="forbid")

    periodo_inicio: date | None = Field(None, description="Data inicial (YYYY-MM-DD)")
    periodo_fim: date | None = Field(None, description="Data final (YYYY-MM-DD)")
    grupo_tecnico: str | None = Field(None, description="Nome exato do grupo técnico")
    categoria: str | None = Field(None, description="Categoria; inclui subcategorias")
    prioridade: int | None = Field(None, ge=1, le=6, description="1 (muito baixa) a 6 (crítica)")
    tipo: TipoChamado | None = None
    entidade: str | None = None

    def filtro(self) -> FiltroChamados:
        return FiltroChamados(**self.model_dump(include=set(ArgsFiltro.model_fields)))


class ArgsVolume(ArgsFiltro):
    granularidade: ind.Granularidade = "dia"


class ArgsBacklog(ArgsFiltro):
    pass


class ArgsSla(ArgsFiltro):
    tipo_sla: ind.TipoSla = Field(description="tto = atendimento (assumir o chamado); ttr = solução")
    dimensao: ind.Dimensao | None = Field(None, description="Quebra opcional do resultado")


class ArgsRisco(ArgsFiltro):
    limite: int = Field(10, ge=1, le=20)


class ArgsTempos(ArgsFiltro):
    pass


class ArgsDistribuicao(ArgsFiltro):
    dimensao: ind.Dimensao = "categoria"
    top_n: int = Field(10, ge=1, le=20)


class ArgsValores(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReferenciaVisualizacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chamada: int = Field(description="Número da chamada de ferramenta a ilustrar")
    titulo: str = Field(min_length=1, max_length=120)


class ArgsResponder(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resposta: str = Field(min_length=1, max_length=2000, description="Resposta final ao usuário")
    visualizacao: ReferenciaVisualizacao | None = None
    filtros_sugeridos: ArgsFiltro | None = Field(None, description="Recorte a aplicar no painel")


# ---------- visualização ----------

class Serie(BaseModel):
    nome: str
    valores: list[float | None]


class Kpi(BaseModel):
    rotulo: str
    valor: float | None
    unidade: str = ""


class Visualizacao(BaseModel):
    tipo: Literal["linha", "barra", "kpi", "tabela"]
    titulo: str
    unidade: str = ""
    categorias: list[str] = []
    series: list[Serie] = []
    kpis: list[Kpi] = []
    colunas: list[str] = []
    linhas: list[list[str | float | int | None]] = []


def _vis_volume(r: ind.Volume, titulo: str) -> Visualizacao:
    return Visualizacao(
        tipo="linha",
        titulo=titulo,
        categorias=[p.periodo for p in r.serie],
        series=[
            Serie(nome="Abertos", valores=[p.abertos for p in r.serie]),
            Serie(nome="Solucionados", valores=[p.solucionados for p in r.serie]),
            Serie(nome="Fechados", valores=[p.fechados for p in r.serie]),
        ],
    )


def _vis_backlog(r: ind.Backlog, titulo: str) -> Visualizacao:
    return Visualizacao(
        tipo="barra",
        titulo=titulo,
        categorias=[f.faixa for f in r.faixas],
        series=[Serie(nome="Chamados abertos", valores=[f.quantidade for f in r.faixas])],
    )


def _vis_sla(r: ind.Sla, titulo: str) -> Visualizacao:
    if r.por_dimensao:
        return Visualizacao(
            tipo="barra",
            titulo=titulo,
            unidade="%",
            categorias=[d.valor for d in r.por_dimensao],
            series=[Serie(nome="% cumprido", valores=[d.percentual for d in r.por_dimensao])],
        )
    if len(r.serie_mensal) > 1:
        return Visualizacao(
            tipo="linha",
            titulo=titulo,
            unidade="%",
            categorias=[m.valor for m in r.serie_mensal],
            series=[Serie(nome="% cumprido", valores=[m.percentual for m in r.serie_mensal])],
        )
    return Visualizacao(
        tipo="kpi",
        titulo=titulo,
        kpis=[
            Kpi(rotulo="Cumprido", valor=r.percentual, unidade="%"),
            Kpi(rotulo="No prazo", valor=r.cumpridos),
            Kpi(rotulo="Elegíveis", valor=r.elegiveis),
        ],
    )


def _vis_risco(r: ind.SlaEmRisco, titulo: str) -> Visualizacao:
    # O frontend pode exibir o título do chamado; ele só não vai ao LLM.
    return Visualizacao(
        tipo="tabela",
        titulo=titulo,
        kpis=[Kpi(rotulo="Vencidos", valor=r.vencidos), Kpi(rotulo="Em risco", valor=r.em_risco)],
        colunas=["ID", "Título", "Grupo técnico", "Prioridade", "Restante (h)", "Situação"],
        linhas=[
            [c.id, c.titulo, ", ".join(c.grupos_tecnicos) or "Sem grupo", c.prioridade, c.horas_restantes,
             "Vencido" if c.situacao == "vencido" else "Em risco"]
            for c in r.itens
        ],
    )


def _vis_tempos(r: ind.Tempos, titulo: str) -> Visualizacao:
    estats = [r.atendimento, r.solucao]
    return Visualizacao(
        tipo="barra",
        titulo=titulo,
        unidade="h",
        categorias=["Atendimento", "Solução"],
        series=[
            Serie(nome="Média", valores=[e.media_horas for e in estats]),
            Serie(nome="Mediana", valores=[e.mediana_horas for e in estats]),
            Serie(nome="P90", valores=[e.p90_horas for e in estats]),
        ],
    )


def _vis_distribuicao(r: ind.Distribuicao, titulo: str) -> Visualizacao:
    itens = [(i.valor, i.quantidade) for i in r.itens] + ([("Outros", r.outros)] if r.outros else [])
    return Visualizacao(
        tipo="barra",
        titulo=titulo,
        categorias=[v for v, _ in itens],
        series=[Serie(nome="Chamados", valores=[q for _, q in itens])],
    )


# ---------- registro ----------

@dataclass(frozen=True)
class Ferramenta:
    nome: str
    descricao: str
    argumentos: type[BaseModel]
    executar: Callable[[ServicoIndicadores, Any], Awaitable[BaseModel]]
    visualizar: Callable[[Any, str], Visualizacao] | None = None


FERRAMENTAS: dict[str, Ferramenta] = {
    f.nome: f
    for f in [
        Ferramenta(
            "consultar_volume",
            "IND-01: quantidade de chamados abertos, solucionados e fechados no período, com série temporal.",
            ArgsVolume,
            lambda s, a: s.volume(a.filtro(), a.granularidade),
            _vis_volume,
        ),
        Ferramenta(
            "consultar_backlog",
            "IND-02: chamados abertos agora, por faixa de idade (aging) e por grupo. Ignora o período.",
            ArgsBacklog,
            lambda s, a: s.backlog(a.filtro()),
            _vis_backlog,
        ),
        Ferramenta(
            "consultar_sla",
            "IND-03/IND-04: percentual de cumprimento do SLA de atendimento (tto) ou de solução (ttr), "
            "com quebra opcional por dimensão e série mensal.",
            ArgsSla,
            lambda s, a: s.sla(a.filtro(), a.tipo_sla, a.dimensao),
            _vis_sla,
        ),
        Ferramenta(
            "listar_sla_em_risco",
            "IND-05: chamados abertos com SLA de solução vencido ou com menos de 20% do prazo restante "
            "(IDs, grupos, prioridade, prazo). Ignora o período.",
            ArgsRisco,
            lambda s, a: s.sla_em_risco(a.filtro(), a.limite),
            _vis_risco,
        ),
        Ferramenta(
            "consultar_tempos",
            "IND-06: média, mediana e p90, em horas, do tempo até assumir e até solucionar.",
            ArgsTempos,
            lambda s, a: s.tempos(a.filtro()),
            _vis_tempos,
        ),
        Ferramenta(
            "consultar_distribuicao",
            "IND-07: chamados abertos no período agrupados por categoria, grupo técnico, prioridade, tipo "
            "ou entidade (top N).",
            ArgsDistribuicao,
            lambda s, a: s.distribuicao(a.filtro(), a.dimensao, a.top_n),
            _vis_distribuicao,
        ),
        Ferramenta(
            "listar_valores_filtro",
            "Nomes válidos de grupos técnicos, categorias, entidades, prioridades e tipos.",
            ArgsValores,
            lambda s, _: s.valores_filtro(),
        ),
    ]
}

RESPONDER = "responder_usuario"
DESCRICAO_RESPONDER = (
    "Entrega a resposta final ao usuário. Chame uma única vez, depois de ver os resultados das ferramentas."
)


def _esquema(modelo: type[BaseModel]) -> dict:
    """JSON Schema com $ref resolvidos (esquemas planos são aceitos por qualquer provedor)."""
    bruto = modelo.model_json_schema()
    definicoes = bruto.pop("$defs", {})

    def resolver(no: Any) -> Any:
        if isinstance(no, dict):
            if "$ref" in no:
                return resolver(definicoes[no["$ref"].split("/")[-1]])
            return {k: resolver(v) for k, v in no.items() if k != "title"}
        if isinstance(no, list):
            return [resolver(v) for v in no]
        return no

    return resolver(bruto)


def definicoes_ferramentas() -> list[dict]:
    """Ferramentas no formato OpenAI/LiteLLM (o LiteLLM converte para o formato de cada provedor)."""
    todas = [(f.nome, f.descricao, f.argumentos) for f in FERRAMENTAS.values()]
    todas.append((RESPONDER, DESCRICAO_RESPONDER, ArgsResponder))
    return [
        {"type": "function", "function": {"name": nome, "description": descricao, "parameters": _esquema(modelo)}}
        for nome, descricao, modelo in todas
    ]


def _remover_campos(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {k: _remover_campos(v) for k, v in valor.items() if k not in CAMPOS_PROIBIDOS_LLM}
    if isinstance(valor, list):
        return [_remover_campos(v) for v in valor]
    return valor


def para_llm(resultado: BaseModel) -> dict:
    """Serializa o resultado de uma ferramenta sem texto livre de chamados."""
    return _remover_campos(resultado.model_dump(mode="json"))


def montar_visualizacao(ferramenta: Ferramenta, resultado: BaseModel, titulo: str) -> Visualizacao | None:
    if ferramenta.visualizar is None:
        return None
    dados = resultado.resultado if isinstance(resultado, RespostaIndicador) else resultado
    return ferramenta.visualizar(dados, titulo)
