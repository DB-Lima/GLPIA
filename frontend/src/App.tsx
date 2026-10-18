import { useState } from "react";
import { api } from "./api/cliente";
import type { Dimensao, Granularidade } from "./api/tipos";
import { BarraFiltros } from "./components/BarraFiltros";
import { Chat } from "./components/Chat";
import { GraficoBacklog, GraficoDistribuicao, GraficoSlaPorDimensao, GraficoVolume } from "./components/Graficos";
import { Kpis } from "./components/Kpis";
import { Painel } from "./components/Painel";
import { TabelaRisco } from "./components/TabelaRisco";
import { useApi } from "./hooks/useApi";
import { useFiltros } from "./hooks/useFiltros";
import { filtrosDaUrl, filtrosParaQuery } from "./lib/filtros";
import { fmtData, fmtDataHora } from "./lib/formato";

const DIMENSOES: [Dimensao, string][] = [
  ["categoria", "Categoria"],
  ["grupo_tecnico", "Grupo técnico"],
  ["prioridade", "Prioridade"],
  ["tipo", "Tipo"],
  ["entidade", "Entidade"],
];

export default function App() {
  const { filtros, alterar, aplicar } = useFiltros();
  const [granularidade, setGranularidade] = useState<Granularidade>("dia");
  const [dimensao, setDimensao] = useState<Dimensao>("categoria");
  const chave = filtrosParaQuery(filtros);

  const valores = useApi(api.valoresFiltro(), "valores");
  const volume = useApi(api.volume(filtros, granularidade), `${chave}|${granularidade}`);
  const backlog = useApi(api.backlog(filtros), chave);
  const slaTto = useApi(api.slaTto(filtros), chave);
  const slaTtr = useApi(api.slaTtr(filtros, "grupo_tecnico"), chave);
  const risco = useApi(api.slaEmRisco(filtros), chave);
  const tempos = useApi(api.tempos(filtros), chave);
  const distribuicao = useApi(api.distribuicao(filtros, dimensao), `${chave}|${dimensao}`);

  const aplicado = volume.dados?.filtro_aplicado;

  return (
    <div className="app">
      <header className="topo">
        <div>
          <h1>GLPIA</h1>
          <p className="subtitulo">Indicadores de SLA e atendimento</p>
        </div>
        {volume.dados && (
          <p className="referencia">
            Período {fmtData(volume.dados.filtro_aplicado.periodo_inicio)} a{" "}
            {fmtData(volume.dados.filtro_aplicado.periodo_fim)} · dados de {fmtDataHora(volume.dados.referencia)}
          </p>
        )}
      </header>

      <BarraFiltros
        filtros={filtros}
        periodoPadrao={aplicado && { inicio: aplicado.periodo_inicio, fim: aplicado.periodo_fim }}
        valores={valores}
        onAlterar={alterar}
        onLimpar={() => aplicar({})}
      />

      <div className="layout">
      <main className="conteudo">
        <Kpis volume={volume} backlog={backlog} slaTto={slaTto} slaTtr={slaTtr} risco={risco} tempos={tempos} />

        <div className="grade">
          <Painel
            titulo="Volume de chamados"
            estado={volume}
            acoes={
              <select
                aria-label="Granularidade"
                value={granularidade}
                onChange={(e) => setGranularidade(e.target.value as Granularidade)}
              >
                <option value="dia">Por dia</option>
                <option value="semana">Por semana</option>
                <option value="mes">Por mês</option>
              </select>
            }
          >
            {(r) => <GraficoVolume volume={r.resultado} />}
          </Painel>

          <Painel titulo="SLA de solução por grupo técnico" estado={slaTtr}>
            {(r) =>
              r.resultado.por_dimensao.length ? (
                <GraficoSlaPorDimensao sla={r.resultado} />
              ) : (
                <p className="estado">Nenhum chamado solucionado com SLA no período.</p>
              )
            }
          </Painel>

          <Painel titulo="Backlog por grupo e idade" estado={backlog}>
            {(r) =>
              r.resultado.total ? (
                <GraficoBacklog backlog={r.resultado} />
              ) : (
                <p className="estado">Nenhum chamado aberto.</p>
              )
            }
          </Painel>

          <Painel
            titulo="Distribuição de chamados abertos no período"
            estado={distribuicao}
            acoes={
              <select aria-label="Dimensão" value={dimensao} onChange={(e) => setDimensao(e.target.value as Dimensao)}>
                {DIMENSOES.map(([v, nome]) => (
                  <option key={v} value={v}>
                    {nome}
                  </option>
                ))}
              </select>
            }
          >
            {(r) =>
              r.resultado.total_chamados ? (
                <GraficoDistribuicao distribuicao={r.resultado} />
              ) : (
                <p className="estado">Nenhum chamado aberto no período.</p>
              )
            }
          </Painel>
        </div>

        <Painel titulo="Chamados com SLA vencido ou em risco" estado={risco} className="largura-total">
          {(r) => <TabelaRisco risco={r.resultado} />}
        </Painel>
      </main>

      <Chat filtros={filtros} onAplicarFiltros={(f) => aplicar(filtrosDaUrl(filtrosParaQuery(f)))} />
      </div>
    </div>
  );
}
