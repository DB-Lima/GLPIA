import { filtrosParaQuery } from "../lib/filtros";
import type {
  Backlog,
  Dimensao,
  Distribuicao,
  Filtros,
  Granularidade,
  RespostaIndicador,
  Sla,
  SlaEmRisco,
  Tempos,
  ValoresFiltro,
  Volume,
} from "./tipos";

export class ErroApi extends Error {}

export async function obterJson<T>(caminho: string, sinal?: AbortSignal): Promise<T> {
  const resposta = await fetch(caminho, { signal: sinal });
  if (!resposta.ok) {
    let detalhe = `${resposta.status} ${resposta.statusText}`;
    try {
      const corpo = await resposta.json();
      if (typeof corpo?.detail === "string") detalhe = corpo.detail;
    } catch {
      // corpo não é JSON; mantém o status
    }
    throw new ErroApi(detalhe);
  }
  return resposta.json() as Promise<T>;
}

function indicador<T>(nome: string, filtros: Filtros, extras: Record<string, string | number> = {}) {
  const query = [filtrosParaQuery(filtros), new URLSearchParams(extras as Record<string, string>).toString()]
    .filter(Boolean)
    .join("&");
  return (sinal?: AbortSignal) =>
    obterJson<RespostaIndicador<T>>(`/api/v1/indicadores/${nome}${query ? `?${query}` : ""}`, sinal);
}

export const api = {
  volume: (f: Filtros, granularidade: Granularidade) => indicador<Volume>("volume", f, { granularidade }),
  backlog: (f: Filtros) => indicador<Backlog>("backlog", f),
  slaTto: (f: Filtros) => indicador<Sla>("sla_tto", f),
  slaTtr: (f: Filtros, dimensao: Dimensao) => indicador<Sla>("sla_ttr", f, { dimensao }),
  slaEmRisco: (f: Filtros) => indicador<SlaEmRisco>("sla_em_risco", f, { limite: 100 }),
  tempos: (f: Filtros) => indicador<Tempos>("tempos", f),
  distribuicao: (f: Filtros, dimensao: Dimensao) => indicador<Distribuicao>("distribuicao", f, { dimensao, top_n: 10 }),
  valoresFiltro: () => (sinal?: AbortSignal) => obterJson<ValoresFiltro>("/api/v1/filtros/valores", sinal),
};
