import type { Filtros, TipoChamado, ValoresFiltro } from "../api/tipos";
import type { EstadoApi } from "../hooks/useApi";

interface Props {
  filtros: Filtros;
  periodoPadrao?: { inicio: string; fim: string };
  valores: EstadoApi<ValoresFiltro>;
  onAlterar: (mudancas: Partial<Filtros>) => void;
  onLimpar: () => void;
}

const NOMES_TIPO: Record<TipoChamado, string> = { incidente: "Incidente", requisicao: "Requisição" };

function Selecao({
  rotulo,
  valor,
  opcoes,
  onChange,
}: {
  rotulo: string;
  valor: string | undefined;
  opcoes: [string, string][];
  onChange: (v: string) => void;
}) {
  return (
    <label className="campo">
      <span>{rotulo}</span>
      <select value={valor ?? ""} onChange={(e) => onChange(e.target.value)}>
        <option value="">Todos</option>
        {opcoes.map(([v, nome]) => (
          <option key={v} value={v}>
            {nome}
          </option>
        ))}
      </select>
    </label>
  );
}

export function BarraFiltros({ filtros, periodoPadrao, valores, onAlterar, onLimpar }: Props) {
  const v = valores.dados;
  const pares = (lista: string[] = []) => lista.map((x) => [x, x] as [string, string]);
  const temFiltro = Object.keys(filtros).length > 0;

  return (
    <form className="barra-filtros" onSubmit={(e) => e.preventDefault()} aria-label="Filtros do painel">
      <label className="campo">
        <span>De</span>
        <input
          type="date"
          value={filtros.periodo_inicio ?? periodoPadrao?.inicio ?? ""}
          onChange={(e) => onAlterar({ periodo_inicio: e.target.value })}
        />
      </label>
      <label className="campo">
        <span>Até</span>
        <input
          type="date"
          value={filtros.periodo_fim ?? periodoPadrao?.fim ?? ""}
          onChange={(e) => onAlterar({ periodo_fim: e.target.value })}
        />
      </label>
      <Selecao
        rotulo="Grupo técnico"
        valor={filtros.grupo_tecnico}
        opcoes={pares(v?.grupos_tecnicos)}
        onChange={(x) => onAlterar({ grupo_tecnico: x })}
      />
      <Selecao
        rotulo="Categoria"
        valor={filtros.categoria}
        opcoes={pares(v?.categorias)}
        onChange={(x) => onAlterar({ categoria: x })}
      />
      <Selecao
        rotulo="Prioridade"
        valor={filtros.prioridade?.toString()}
        opcoes={Object.entries(v?.prioridades ?? {})}
        onChange={(x) => onAlterar({ prioridade: x ? Number(x) : undefined })}
      />
      <Selecao
        rotulo="Tipo"
        valor={filtros.tipo}
        opcoes={(v?.tipos ?? []).map((t) => [t, NOMES_TIPO[t]] as [string, string])}
        onChange={(x) => onAlterar({ tipo: (x || undefined) as TipoChamado | undefined })}
      />
      <Selecao
        rotulo="Entidade"
        valor={filtros.entidade}
        opcoes={pares(v?.entidades)}
        onChange={(x) => onAlterar({ entidade: x })}
      />
      <button type="button" className="botao-secundario" onClick={onLimpar} disabled={!temFiltro}>
        Limpar filtros
      </button>
      {valores.erro && <p className="estado erro">Filtros indisponíveis: {valores.erro}</p>}
    </form>
  );
}
