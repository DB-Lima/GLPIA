# 01 — Catálogo de indicadores

Fonte única de verdade para fórmulas. Backend, ferramentas da IA e testes
devem seguir exatamente estas definições. Detalhes do modelo GLPI em
[agent_docs/glpi-dominio.md](../agent_docs/glpi-dominio.md).

## Filtros comuns

Todos os indicadores aceitam os mesmos filtros (todos opcionais):

| Filtro | Campo GLPI | Observação |
|---|---|---|
| `periodo_inicio`, `periodo_fim` | `date` (abertura) | Padrão: últimos 30 dias. Indicadores de solução usam `solvedate` |
| `grupo_tecnico` | `glpi_groups_tickets` com `type = 2` (atribuído) | Pode haver mais de um grupo por chamado |
| `categoria` | `itilcategories_id` | Inclui subcategorias quando `incluir_subcategorias = true` |
| `prioridade` | `priority` (1 a 6) | |
| `tipo` | `type` (1 = incidente, 2 = requisição) | |
| `entidade` | `entities_id` | |

## Indicadores

### IND-01 — Volume de chamados (MVP)
- **Pergunta que responde:** quantos chamados foram abertos, solucionados e fechados?
- **Fórmula:** contagem por `date`, `solvedate` e `closedate` dentro do período.
- **Granularidade:** dia, semana ou mês.
- **Visualização:** linha (série temporal) + cards de total.

### IND-02 — Backlog e aging (MVP)
- **Pergunta:** quantos chamados estão abertos agora e há quanto tempo?
- **Fórmula:** chamados com `status` em {1, 2, 3, 4}; idade = agora − `date`.
- **Faixas de aging:** 0–2 d, 3–7 d, 8–15 d, 16–30 d, > 30 d.
- **Visualização:** barras empilhadas por faixa e grupo.

### IND-03 — Cumprimento de SLA de atendimento (TTO) (MVP)
- **Pergunta:** que % dos chamados foi assumido dentro do prazo?
- **Fórmula:** `cumpridos / elegíveis × 100`, onde
  - elegíveis: chamados com `time_to_own` preenchido e já assumidos
    (`takeintoaccountdate` não nulo) no período;
  - cumprido: `takeintoaccountdate <= time_to_own`.
- **Visualização:** card com % + linha de tendência mensal.

### IND-04 — Cumprimento de SLA de solução (TTR) (MVP)
- **Pergunta:** que % dos chamados foi solucionado dentro do prazo?
- **Fórmula:** `cumpridos / elegíveis × 100`, onde
  - elegíveis: chamados com `time_to_resolve` preenchido e `solvedate` no período;
  - cumprido: `solvedate <= time_to_resolve`.
- **Visualização:** card com % + barras por grupo.

### IND-05 — Chamados com SLA vencido ou em risco (MVP)
- **Pergunta:** quais chamados abertos já estouraram ou estão perto de estourar?
- **Fórmula:** para chamados abertos com `time_to_resolve`:
  - vencido: agora > `time_to_resolve`;
  - em risco: tempo restante < 20% do prazo total (`time_to_resolve − date`).
- **Visualização:** tabela (ID, título, grupo, prioridade, prazo, situação).
- **Privacidade:** a tabela exibe título do chamado no painel, mas o título
  **não** é enviado ao LLM (ver ADR-0004).

### IND-06 — Tempo médio de atendimento e de solução (MVP)
- **Pergunta:** quanto tempo levamos para assumir e resolver?
- **Fórmula:** média, mediana e p90 de
  - atendimento: `takeintoaccount_delay_stat` (segundos);
  - solução: `solve_delay_stat` (segundos).
- **Nota:** os campos `*_delay_stat` do GLPI já descontam o calendário do SLA
  quando configurado; usar diferença de datas apenas como fallback.
- **Visualização:** cards em horas + boxplot por grupo (pós-MVP).

### IND-07 — Distribuição por dimensão (MVP)
- **Pergunta:** onde se concentra a demanda?
- **Fórmula:** contagem de chamados abertos no período agrupada por uma
  dimensão: categoria, grupo técnico, prioridade, tipo ou entidade. Top N (padrão 10).
- **Visualização:** barras horizontais.

### IND-08 — Satisfação (CSAT) (pós-MVP)
- **Pergunta:** os usuários estão satisfeitos?
- **Fórmula:** média de `glpi_ticketsatisfactions.satisfaction` (0–5) com
  `date_answered` no período; taxa de resposta = respondidas / enviadas.
- **Visualização:** card + linha mensal.

### IND-09 — Taxa de solução no primeiro nível (pós-MVP)
- **Pergunta:** quanto o N1 resolve sem escalar?
- **Fórmula:** a definir com a área (depende de como o GLPI registra escalonamento).

## Regras gerais

- Datas armazenadas e calculadas em `America/Sao_Paulo`.
- Chamados excluídos (`is_deleted = 1`) nunca entram em nenhum indicador.
- Percentuais com 1 casa decimal; tempos exibidos em horas com 1 casa.
- Todo indicador retorna junto o filtro efetivamente aplicado, para que a IA
  e o painel exibam o mesmo contexto.
