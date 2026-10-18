import type { Backlog, RespostaIndicador, Sla, SlaEmRisco, Tempos, Volume } from "../api/tipos";
import type { EstadoApi } from "../hooks/useApi";
import { fmtHoras, fmtNumero, fmtPct } from "../lib/formato";

type Estado<T> = EstadoApi<RespostaIndicador<T>>;

interface Props {
  volume: Estado<Volume>;
  backlog: Estado<Backlog>;
  slaTto: Estado<Sla>;
  slaTtr: Estado<Sla>;
  risco: Estado<SlaEmRisco>;
  tempos: Estado<Tempos>;
}

function Kpi<T>({
  rotulo,
  estado,
  valor,
  detalhe,
  destaque,
}: {
  rotulo: string;
  estado: Estado<T>;
  valor: (r: T) => string;
  detalhe?: (r: T) => string;
  destaque?: (r: T) => boolean;
}) {
  const r = estado.dados?.resultado;
  return (
    <div className={`kpi${r && destaque?.(r) ? " kpi-alerta" : ""}`} aria-busy={estado.carregando}>
      <span className="kpi-rotulo">{rotulo}</span>
      {estado.erro ? (
        <span className="estado erro">Erro</span>
      ) : r ? (
        <>
          <strong className="kpi-valor">{valor(r)}</strong>
          {detalhe && <span className="kpi-detalhe">{detalhe(r)}</span>}
        </>
      ) : (
        <span className="estado">…</span>
      )}
    </div>
  );
}

export function Kpis({ volume, backlog, slaTto, slaTtr, risco, tempos }: Props) {
  return (
    <div className="kpis">
      <Kpi
        rotulo="Abertos no período"
        estado={volume}
        valor={(r) => fmtNumero(r.abertos)}
        detalhe={(r) => `${fmtNumero(r.solucionados)} solucionados`}
      />
      <Kpi rotulo="Backlog atual" estado={backlog} valor={(r) => fmtNumero(r.total)} detalhe={() => "chamados abertos"} />
      <Kpi
        rotulo="SLA de atendimento (TTO)"
        estado={slaTto}
        valor={(r) => fmtPct(r.percentual)}
        detalhe={(r) => `${r.cumpridos} de ${r.elegiveis}`}
      />
      <Kpi
        rotulo="SLA de solução (TTR)"
        estado={slaTtr}
        valor={(r) => fmtPct(r.percentual)}
        detalhe={(r) => `${r.cumpridos} de ${r.elegiveis}`}
      />
      <Kpi
        rotulo="SLA vencido"
        estado={risco}
        valor={(r) => fmtNumero(r.vencidos)}
        detalhe={(r) => `${r.em_risco} em risco`}
        destaque={(r) => r.vencidos > 0}
      />
      <Kpi
        rotulo="Mediana de solução"
        estado={tempos}
        valor={(r) => fmtHoras(r.solucao.mediana_horas)}
        detalhe={(r) => `atendimento: ${fmtHoras(r.atendimento.mediana_horas)}`}
      />
    </div>
  );
}
