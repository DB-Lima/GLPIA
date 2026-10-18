# 03 — Roadmap

Cada entrega corresponde a uma spec em [`specs/`](../specs/). Uma spec só é
executada depois de revisada e com `locked_at` preenchido no momento em que a
tarefa é entregue ao agente (ver [agent_docs/sdd-workflow.md](../agent_docs/sdd-workflow.md)).

## Fase 1 — MVP local (dados mock)

| Ordem | Spec | Entrega | Depende de |
|---|---|---|---|
| 0 | SPEC-2026-0001 | Documentação inicial (este conjunto) | — |
| 1 | SPEC-2026-0002 | Backend FastAPI + modelo normalizado + adapter mock com dataset fictício | 0001 |
| 2 | SPEC-2026-0003 | Serviço de indicadores IND-01 a IND-07 + endpoints REST | 0002 |
| 3 | SPEC-2026-0004 | Frontend React: painel com filtros, cards, gráficos e tabela de SLA em risco | 0003 |
| 4 | SPEC-2026-0005 | Chat com IA (LiteLLM + Claude, tool calling, schema de resposta, filtros sugeridos) | 0003 (front: 0004) |

**Pronto quando:** o fluxo de [02-arquitetura.md](02-arquitetura.md) funciona de
ponta a ponta localmente e os números da IA batem com os do painel.

## Fase 2 — Dados reais

| Spec | Entrega |
|---|---|
| SPEC-2026-0006 | Adapter REST do GLPI (sessão, paginação, mapeamento, cache) |
| a criar | Cache Redis e atualização incremental |
| a criar | IND-08 (CSAT) e IND-09 (resolução no N1) |

## Fase 3 — Preparação para a esteira da TI

| Entrega | Referência |
|---|---|
| OpenTelemetry + OpenLIT, logs JSON com `trace_id`, envio a Langfuse | padrões de observabilidade |
| SSO Azure AD (SPA + PKCE) e RBAC por grupo/entidade | aprovação prévia |
| Dockerfiles UBI, manifests `k8s/`, `.gitlab-ci.yml` | padrão CI/CD e K8s |
| Diagrama de FinOps (custo por pergunta, tokens) | exigido no Tier 2 |
| Separação em repositórios formais | [ADR-0005](adr/ADR-0005-monorepo-no-mvp.md) |
| Submissão Arquitetura + SI | [04-governanca.md](04-governanca.md) |

## Backlog de ideias (sem compromisso)

- Alertas proativos de SLA em risco (e-mail/Teams).
- Perguntas sobre conteúdo dos chamados com modelo local (modo soberano).
- Migrar o agente para LangGraph se surgirem fluxos com múltiplos passos e memória.
