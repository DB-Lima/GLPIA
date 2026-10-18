# GLPIA

Dashboard de indicadores de SLA e atendimento do GLPI com um assistente de IA
que responde perguntas em linguagem natural e ajusta os filtros do painel.

> **Status:** documentação inicial. Código do MVP começa pela SPEC-2026-0002.

## O que o MVP vai entregar

- Painel com volume, backlog/aging, cumprimento de SLA (TTO e TTR), chamados em
  risco, tempos médios e distribuição por categoria/grupo/prioridade.
- Chat com IA: "qual o SLA de solução do N2 em setembro?" → resposta em texto,
  gráfico e sugestão de filtros para o painel.
- Dados fictícios no formato do GLPI (mock); conexão com a API REST real na fase 2.

## Documentação

| Documento | Conteúdo |
|---|---|
| [Visão do produto](docs/00-visao-produto.md) | Problema, público, escopo do MVP |
| [Indicadores](docs/01-indicadores.md) | Fórmulas e campos de origem no GLPI |
| [Arquitetura](docs/02-arquitetura.md) | Contêineres, fluxo da IA, ferramentas |
| [Roadmap](docs/03-roadmap.md) | Fases e specs |
| [Governança](docs/04-governanca.md) | Tier, privacidade, pendências |
| [ADRs](docs/adr/) | Decisões de arquitetura |
| [Diagramas](docs/diagramas/) | C4-PlantUML |
| [Specs](specs/) | Spec-Driven Development: uma spec por entrega |

## Como o projeto usa IA no desenvolvimento

1. Cada entrega tem uma spec (`specs/SPEC-2026-NNNN.yaml`) com critérios de
   aceite verificáveis, escrita **antes** da execução.
2. O agente (Claude Code) lê o `CLAUDE.md` e os arquivos de `agent_docs/` para
   ter o contexto do projeto sem reexplicação.
3. Decisões viram ADRs; os critérios de aceite viram o checklist do PR.

Comandos do projeto no Claude Code: `/nova-spec` e `/travar-spec`.

## Stack

React 18 + Vite + TypeScript · FastAPI (Python 3.12) · LiteLLM + Claude
