import { useEffect, useRef, useState } from "react";
import { perguntar } from "../api/cliente";
import type { Filtros, MensagemHistorico, RespostaChat } from "../api/tipos";
import { GraficoIA } from "./GraficoIA";

interface Mensagem {
  papel: "usuario" | "assistente";
  texto: string;
  resposta?: RespostaChat;
  erro?: boolean;
}

interface Props {
  filtros: Filtros;
  onAplicarFiltros: (filtros: Filtros) => void;
}

const EXEMPLOS = [
  "Qual o SLA de solução por grupo técnico neste período?",
  "Quantos chamados estão com SLA vencido no N2?",
  "Como está o backlog por idade?",
  "Quais categorias mais abriram chamados em setembro?",
];

export function Chat({ filtros, onAplicarFiltros }: Props) {
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const fim = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Sem retorno: em navegadores recentes scrollIntoView devolve uma Promise, que o React trataria como cleanup.
    fim.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [mensagens, enviando]);

  async function enviar(pergunta: string) {
    const limpa = pergunta.trim();
    if (!limpa || enviando) return;
    const historico: MensagemHistorico[] = mensagens
      .filter((m) => !m.erro)
      .slice(-10)
      .map(({ papel, texto }) => ({ papel, texto }));
    setMensagens((atual) => [...atual, { papel: "usuario", texto: limpa }]);
    setTexto("");
    setEnviando(true);
    try {
      const resposta = await perguntar(limpa, historico, filtros);
      setMensagens((atual) => [...atual, { papel: "assistente", texto: resposta.resposta, resposta }]);
    } catch (erro) {
      const msg = erro instanceof Error ? erro.message : "Erro desconhecido";
      setMensagens((atual) => [...atual, { papel: "assistente", texto: msg, erro: true }]);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <aside className="chat" aria-label="Assistente de IA">
      <header className="chat-cabecalho">
        <h2>Pergunte ao GLPIA</h2>
        <p>Respostas calculadas pelas mesmas fórmulas do painel. A IA só lê dados agregados.</p>
      </header>

      <div className="chat-mensagens" aria-live="polite">
        {mensagens.length === 0 && (
          <div className="chat-exemplos">
            {EXEMPLOS.map((e) => (
              <button key={e} type="button" className="exemplo" onClick={() => enviar(e)}>
                {e}
              </button>
            ))}
          </div>
        )}
        {mensagens.map((m, i) => (
          <div key={i} className={`mensagem mensagem-${m.papel}${m.erro ? " mensagem-erro" : ""}`}>
            <p>{m.texto}</p>
            {m.resposta?.visualizacao && <GraficoIA vis={m.resposta.visualizacao} />}
            {m.resposta?.filtros_sugeridos && (
              <button
                type="button"
                className="botao-primario"
                onClick={() => onAplicarFiltros(m.resposta!.filtros_sugeridos!)}
              >
                Aplicar filtros ao painel
              </button>
            )}
            {m.resposta && m.resposta.rastreio.length > 0 && (
              <details className="rastreio">
                <summary>Como calculei</summary>
                <ul>
                  {m.resposta.rastreio.map((r) => (
                    <li key={r.chamada}>
                      <code>{r.ferramenta}</code> {JSON.stringify(r.argumentos)}
                    </li>
                  ))}
                </ul>
                <small>
                  {m.resposta.modelo} · trace {m.resposta.trace_id.slice(0, 8)}
                </small>
              </details>
            )}
          </div>
        ))}
        {enviando && <div className="mensagem mensagem-assistente digitando">Consultando os indicadores…</div>}
        <div ref={fim} />
      </div>

      <form
        className="chat-entrada"
        onSubmit={(e) => {
          e.preventDefault();
          enviar(texto);
        }}
      >
        <textarea
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              enviar(texto);
            }
          }}
          placeholder="Ex.: qual o SLA de solução do N2 em setembro?"
          rows={2}
          maxLength={2000}
          aria-label="Pergunta"
        />
        <button type="submit" className="botao-primario" disabled={enviando || !texto.trim()}>
          Enviar
        </button>
      </form>
    </aside>
  );
}
