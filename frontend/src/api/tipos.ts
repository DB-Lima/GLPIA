// Espelha os modelos de backend/app/domain (models.py e indicadores.py).

export type TipoChamado = "incidente" | "requisicao";
export type Dimensao = "categoria" | "grupo_tecnico" | "prioridade" | "tipo" | "entidade";
export type Granularidade = "dia" | "semana" | "mes";

export interface Filtros {
  periodo_inicio?: string;
  periodo_fim?: string;
  grupo_tecnico?: string;
  categoria?: string;
  prioridade?: number;
  tipo?: TipoChamado;
  entidade?: string;
}

export interface FiltroAplicado extends Filtros {
  periodo_inicio: string;
  periodo_fim: string;
  incluir_subcategorias: boolean;
  incluir_excluidos: boolean;
}

export interface RespostaIndicador<T> {
  filtro_aplicado: FiltroAplicado;
  referencia: string;
  resultado: T;
}

export interface PontoVolume {
  periodo: string;
  abertos: number;
  solucionados: number;
  fechados: number;
}

export interface Volume {
  granularidade: Granularidade;
  abertos: number;
  solucionados: number;
  fechados: number;
  serie: PontoVolume[];
}

export interface FaixaAging {
  faixa: string;
  quantidade: number;
}

export interface Backlog {
  total: number;
  faixas: FaixaAging[];
  por_grupo: { grupo: string; total: number; faixas: FaixaAging[] }[];
}

export interface ContagemSla {
  valor: string;
  percentual: number | null;
  cumpridos: number;
  elegiveis: number;
}

export interface Sla {
  tipo: "tto" | "ttr";
  percentual: number | null;
  cumpridos: number;
  elegiveis: number;
  dimensao: Dimensao | null;
  por_dimensao: ContagemSla[];
  serie_mensal: ContagemSla[];
}

export interface ChamadoEmRisco {
  id: number;
  titulo: string;
  grupos_tecnicos: string[];
  prioridade: number;
  prazo_ttr: string;
  horas_restantes: number;
  situacao: "vencido" | "em_risco";
}

export interface SlaEmRisco {
  vencidos: number;
  em_risco: number;
  itens: ChamadoEmRisco[];
}

export interface Estatistica {
  quantidade: number;
  media_horas: number | null;
  mediana_horas: number | null;
  p90_horas: number | null;
}

export interface Tempos {
  atendimento: Estatistica;
  solucao: Estatistica;
}

export interface Distribuicao {
  dimensao: Dimensao;
  total_chamados: number;
  itens: { valor: string; quantidade: number }[];
  outros: number;
}

export interface ValoresFiltro {
  grupos_tecnicos: string[];
  categorias: string[];
  entidades: string[];
  prioridades: Record<string, string>;
  tipos: TipoChamado[];
}

// ---------- chat (backend/app/ai) ----------

export interface Visualizacao {
  tipo: "linha" | "barra" | "kpi" | "tabela";
  titulo: string;
  unidade: string;
  categorias: string[];
  series: { nome: string; valores: (number | null)[] }[];
  kpis: { rotulo: string; valor: number | null; unidade: string }[];
  colunas: string[];
  linhas: (string | number | null)[][];
}

export interface ItemRastreio {
  chamada: number;
  ferramenta: string;
  argumentos: Record<string, unknown>;
}

export interface RespostaChat {
  resposta: string;
  visualizacao: Visualizacao | null;
  filtros_sugeridos: Filtros | null;
  rastreio: ItemRastreio[];
  trace_id: string;
  modelo: string;
}

export interface MensagemHistorico {
  papel: "usuario" | "assistente";
  texto: string;
}
