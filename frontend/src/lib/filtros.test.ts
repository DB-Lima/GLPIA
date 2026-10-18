import { describe, expect, it } from "vitest";
import { filtrosDaUrl, filtrosParaQuery, mesclarFiltros } from "./filtros";

describe("filtros na URL", () => {
  it("ida e volta preserva todos os filtros", () => {
    const filtros = {
      periodo_inicio: "2026-09-01",
      periodo_fim: "2026-09-30",
      grupo_tecnico: "N2 - Suporte Técnico",
      categoria: "Hardware",
      prioridade: 4,
      tipo: "incidente" as const,
      entidade: "Raiz > Unidade Curitiba",
    };
    expect(filtrosDaUrl(filtrosParaQuery(filtros))).toEqual(filtros);
  });

  it("descarta valores inválidos", () => {
    expect(filtrosDaUrl("?periodo_inicio=ontem&prioridade=9&tipo=bug&grupo_tecnico=")).toEqual({});
  });

  it("serializa em ordem fixa e omite vazios", () => {
    expect(filtrosParaQuery({ tipo: "requisicao", periodo_inicio: "2026-10-01", categoria: "" })).toBe(
      "periodo_inicio=2026-10-01&tipo=requisicao",
    );
  });

  it("mesclar remove filtro com valor vazio", () => {
    expect(mesclarFiltros({ grupo_tecnico: "N1", tipo: "incidente" }, { grupo_tecnico: "", prioridade: 3 })).toEqual({
      tipo: "incidente",
      prioridade: 3,
    });
  });
});
