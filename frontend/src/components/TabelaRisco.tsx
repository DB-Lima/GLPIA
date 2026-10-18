import type { SlaEmRisco } from "../api/tipos";
import { fmtDataHora, fmtHoras } from "../lib/formato";

export function TabelaRisco({ risco }: { risco: SlaEmRisco }) {
  if (risco.itens.length === 0) return <p className="estado">Nenhum chamado aberto com SLA vencido ou em risco.</p>;
  return (
    <div className="tabela-rolagem">
      <table className="tabela">
        <thead>
          <tr>
            <th>ID</th>
            <th>Título</th>
            <th>Grupo técnico</th>
            <th>Prioridade</th>
            <th>Prazo de solução</th>
            <th>Restante</th>
            <th>Situação</th>
          </tr>
        </thead>
        <tbody>
          {risco.itens.map((c) => (
            <tr key={c.id} className={c.situacao === "vencido" ? "linha-vencida" : "linha-risco"}>
              <td>{c.id}</td>
              <td>{c.titulo}</td>
              <td>{c.grupos_tecnicos.join(", ") || "Sem grupo"}</td>
              <td>{c.prioridade}</td>
              <td>{fmtDataHora(c.prazo_ttr)}</td>
              <td>{fmtHoras(c.horas_restantes)}</td>
              <td>
                <span className={`selo selo-${c.situacao}`}>{c.situacao === "vencido" ? "Vencido" : "Em risco"}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {risco.vencidos + risco.em_risco > risco.itens.length && (
        <p className="nota">
          Exibindo {risco.itens.length} de {risco.vencidos + risco.em_risco} chamados.
        </p>
      )}
    </div>
  );
}
