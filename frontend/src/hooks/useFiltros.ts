import { useCallback, useEffect, useState } from "react";
import type { Filtros } from "../api/tipos";
import { filtrosDaUrl, filtrosParaQuery, mesclarFiltros } from "../lib/filtros";

/** Filtros do painel sincronizados com a query string (recarregar ou compartilhar a URL mantém o estado). */
export function useFiltros() {
  const [filtros, setFiltros] = useState<Filtros>(() => filtrosDaUrl(window.location.search));

  useEffect(() => {
    const aoNavegar = () => setFiltros(filtrosDaUrl(window.location.search));
    window.addEventListener("popstate", aoNavegar);
    return () => window.removeEventListener("popstate", aoNavegar);
  }, []);

  const aplicar = useCallback((novos: Filtros) => {
    const query = filtrosParaQuery(novos);
    window.history.pushState(null, "", query ? `?${query}` : window.location.pathname);
    setFiltros(novos);
  }, []);

  const alterar = useCallback(
    (mudancas: Partial<Filtros>) => aplicar(mesclarFiltros(filtros, mudancas)),
    [filtros, aplicar],
  );

  return { filtros, alterar, aplicar };
}
