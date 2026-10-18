import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Visualizacao } from "../api/tipos";
import { CORES } from "./Graficos";

const EIXO = { stroke: "var(--texto-suave)", fontSize: 11 };
const fmt = (v: number | null, unidade: string) =>
  v === null ? "—" : `${v.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}${unidade === "%" ? "%" : unidade ? ` ${unidade}` : ""}`;

/** Renderiza a visualização montada pelo backend a partir do resultado real de uma ferramenta. */
export function GraficoIA({ vis }: { vis: Visualizacao }) {
  const dados = vis.categorias.map((categoria, i) => ({
    categoria,
    ...Object.fromEntries(vis.series.map((s) => [s.nome, s.valores[i]])),
  }));
  const dica = (
    <Tooltip
      contentStyle={{ background: "var(--superficie)", border: "1px solid var(--borda)" }}
      formatter={(v) => fmt(v as number | null, vis.unidade)}
    />
  );

  return (
    <figure className="grafico-ia">
      <figcaption>{vis.titulo}</figcaption>
      {vis.kpis.length > 0 && (
        <div className="kpis-ia">
          {vis.kpis.map((k) => (
            <div key={k.rotulo} className="kpi-ia">
              <span>{k.rotulo}</span>
              <strong>{fmt(k.valor, k.unidade)}</strong>
            </div>
          ))}
        </div>
      )}
      {vis.tipo === "linha" && (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={dados} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid stroke="var(--borda)" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="categoria" tick={EIXO} minTickGap={20} />
            <YAxis tick={EIXO} />
            {dica}
            {vis.series.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
            {vis.series.map((s, i) => (
              <Line key={s.nome} dataKey={s.nome} stroke={CORES[i % CORES.length]} dot={false} strokeWidth={2} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
      {vis.tipo === "barra" && (
        <ResponsiveContainer width="100%" height={Math.max(160, dados.length * 28 + 40)}>
          <BarChart data={dados} layout="vertical" margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="var(--borda)" strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={EIXO} />
            <YAxis type="category" dataKey="categoria" tick={EIXO} width={120} />
            {dica}
            {vis.series.length > 1 && <Legend wrapperStyle={{ fontSize: 11 }} />}
            {vis.series.map((s, i) => (
              <Bar key={s.nome} dataKey={s.nome} fill={CORES[i % CORES.length]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      )}
      {vis.tipo === "tabela" && vis.linhas.length > 0 && (
        <div className="tabela-rolagem tabela-ia">
          <table className="tabela">
            <thead>
              <tr>
                {vis.colunas.map((c) => (
                  <th key={c}>{c}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {vis.linhas.map((linha, i) => (
                <tr key={i}>
                  {linha.map((celula, j) => (
                    <td key={j}>{celula ?? "—"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </figure>
  );
}
