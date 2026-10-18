import type { ReactNode } from "react";
import type { EstadoApi } from "../hooks/useApi";

interface Props<T> {
  titulo: string;
  estado: EstadoApi<T>;
  acoes?: ReactNode;
  className?: string;
  children: (dados: T) => ReactNode;
}

/** Cartão com título e tratamento padrão de carregamento, erro e dados. */
export function Painel<T>({ titulo, estado, acoes, className = "", children }: Props<T>) {
  return (
    <section className={`painel ${className}`} aria-busy={estado.carregando}>
      <header className="painel-cabecalho">
        <h2>{titulo}</h2>
        {acoes}
      </header>
      <div className="painel-corpo">
        {estado.erro ? (
          <p className="estado erro" role="alert">
            Não foi possível carregar: {estado.erro}
          </p>
        ) : estado.dados === null ? (
          <p className="estado">Carregando…</p>
        ) : (
          <div className={estado.carregando ? "atualizando" : undefined}>{children(estado.dados)}</div>
        )}
      </div>
    </section>
  );
}
