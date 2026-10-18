import type { Filtros, TipoChamado } from "../api/tipos";

const CHAVES: (keyof Filtros)[] = [
  "periodo_inicio",
  "periodo_fim",
  "grupo_tecnico",
  "categoria",
  "prioridade",
  "tipo",
  "entidade",
];

const TIPOS: TipoChamado[] = ["incidente", "requisicao"];
const DATA = /^\d{4}-\d{2}-\d{2}$/;

/** Lê os filtros da query string, descartando valores inválidos. */
export function filtrosDaUrl(search: string): Filtros {
  const params = new URLSearchParams(search);
  const filtros: Filtros = {};
  for (const chave of ["periodo_inicio", "periodo_fim"] as const) {
    const valor = params.get(chave);
    if (valor && DATA.test(valor)) filtros[chave] = valor;
  }
  for (const chave of ["grupo_tecnico", "categoria", "entidade"] as const) {
    const valor = params.get(chave);
    if (valor) filtros[chave] = valor;
  }
  const prioridade = Number(params.get("prioridade"));
  if (Number.isInteger(prioridade) && prioridade >= 1 && prioridade <= 6) filtros.prioridade = prioridade;
  const tipo = params.get("tipo") as TipoChamado | null;
  if (tipo && TIPOS.includes(tipo)) filtros.tipo = tipo;
  return filtros;
}

/** Serializa os filtros em ordem fixa, omitindo vazios (URL estável e compartilhável). */
export function filtrosParaQuery(filtros: Filtros): string {
  const params = new URLSearchParams();
  for (const chave of CHAVES) {
    const valor = filtros[chave];
    if (valor !== undefined && valor !== "") params.set(chave, String(valor));
  }
  return params.toString();
}

/** Mescla alterações; valor vazio ou undefined remove o filtro. */
export function mesclarFiltros(atual: Filtros, mudancas: Partial<Filtros>): Filtros {
  const novo: Filtros = { ...atual };
  for (const [chave, valor] of Object.entries(mudancas) as [keyof Filtros, Filtros[keyof Filtros]][]) {
    if (valor === undefined || valor === "" || valor === null) delete novo[chave];
    else (novo as Record<string, unknown>)[chave] = valor;
  }
  return novo;
}
