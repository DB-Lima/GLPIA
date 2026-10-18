import { useEffect, useState } from "react";

export interface EstadoApi<T> {
  dados: T | null;
  carregando: boolean;
  erro: string | null;
}

/** Executa a consulta sempre que `chave` muda; cancela a anterior para evitar corrida de respostas. */
export function useApi<T>(consulta: (sinal: AbortSignal) => Promise<T>, chave: string): EstadoApi<T> {
  const [estado, setEstado] = useState<EstadoApi<T>>({ dados: null, carregando: true, erro: null });

  useEffect(() => {
    const controle = new AbortController();
    setEstado((anterior) => ({ ...anterior, carregando: true, erro: null }));
    consulta(controle.signal)
      .then((dados) => setEstado({ dados, carregando: false, erro: null }))
      .catch((erro: unknown) => {
        if (controle.signal.aborted) return;
        const mensagem = erro instanceof Error ? erro.message : "Erro desconhecido";
        setEstado({ dados: null, carregando: false, erro: mensagem });
      });
    return () => controle.abort();
    // `consulta` é recriada a cada render; `chave` representa seus parâmetros.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave]);

  return estado;
}
