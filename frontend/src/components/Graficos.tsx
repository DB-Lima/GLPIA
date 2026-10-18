import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Backlog, Distribuicao, Sla, Volume } from "../api/tipos";
import { fmtNumero, fmtPct } from "../lib/formato";

export const CORES = ["var(--serie-1)", "var(--serie-2)", "var(--serie-3)", "var(--serie-4)", "var(--serie-5)"];
const EIXO = { stroke: "var(--texto-suave)", fontSize: 12 };
const GRADE = <CartesianGrid stroke="var(--borda)" strokeDasharray="3 3" vertical={false} />;
const DICA = <Tooltip contentStyle={{ background: "var(--superficie)", border: "1px solid var(--borda)" }} />;

export function GraficoVolume({ volume }: { volume: Volume }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={volume.serie} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
        {GRADE}
        <XAxis dataKey="periodo" tick={EIXO} minTickGap={24} />
        <YAxis tick={EIXO} allowDecimals={false} width={40} />
        {DICA}
        <Legend />
        <Line type="monotone" dataKey="abertos" name="Abertos" stroke={CORES[0]} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="solucionados" name="Solucionados" stroke={CORES[1]} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="fechados" name="Fechados" stroke={CORES[2]} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function GraficoBacklog({ backlog }: { backlog: Backlog }) {
  const faixas = backlog.faixas.map((f) => f.faixa);
  const linhas = backlog.por_grupo.map((g) => ({
    grupo: g.grupo,
    ...Object.fromEntries(g.faixas.map((f) => [f.faixa, f.quantidade])),
  }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, linhas.length * 34 + 60)}>
      <BarChart data={linhas} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="var(--borda)" strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={EIXO} allowDecimals={false} />
        <YAxis type="category" dataKey="grupo" tick={EIXO} width={150} />
        {DICA}
        <Legend />
        {faixas.map((faixa, i) => (
          <Bar key={faixa} dataKey={faixa} stackId="aging" fill={CORES[i % CORES.length]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function GraficoSlaPorDimensao({ sla }: { sla: Sla }) {
  const dados = sla.por_dimensao.map((d) => ({ ...d, percentual: d.percentual ?? 0 }));
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, dados.length * 34 + 40)}>
      <BarChart data={dados} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="var(--borda)" strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={EIXO} unit="%" />
        <YAxis type="category" dataKey="valor" tick={EIXO} width={150} />
        <Tooltip
          contentStyle={{ background: "var(--superficie)", border: "1px solid var(--borda)" }}
          formatter={(_v, _n, item) => {
            const d = item.payload as Sla["por_dimensao"][number];
            return [`${fmtPct(d.percentual)} (${d.cumpridos} de ${d.elegiveis})`, "Cumprido"];
          }}
        />
        <Bar dataKey="percentual" name="% cumprido" fill={CORES[1]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function GraficoDistribuicao({ distribuicao }: { distribuicao: Distribuicao }) {
  const dados = [...distribuicao.itens];
  if (distribuicao.outros > 0) dados.push({ valor: "Outros", quantidade: distribuicao.outros });
  return (
    <ResponsiveContainer width="100%" height={Math.max(220, dados.length * 30 + 40)}>
      <BarChart data={dados} layout="vertical" margin={{ top: 8, right: 24, left: 8, bottom: 0 }}>
        <CartesianGrid stroke="var(--borda)" strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={EIXO} allowDecimals={false} />
        <YAxis type="category" dataKey="valor" tick={EIXO} width={170} />
        <Tooltip
          contentStyle={{ background: "var(--superficie)", border: "1px solid var(--borda)" }}
          formatter={(v) => [fmtNumero(Number(v)), "Chamados"]}
        />
        <Bar dataKey="quantidade" name="Chamados" fill={CORES[0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
