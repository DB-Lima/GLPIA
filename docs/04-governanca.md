# 04 — Governança, classificação e conformidade

## Precisa da esteira de aprovação agora?

**Não.** Enquanto o projeto roda só localmente, a iniciativa está no escopo
**Local** e não passa pela esteira de Arquitetura + SI. A esteira passa a ser
necessária quando o GLPIA for **compartilhado como serviço web** (stack
Web based/GitLab) — ou seja, antes de qualquer deploy em QA/PRD com
usuários reais.

> Antes de submeter, conferir no InovaTrack se já existe iniciativa
> semelhante (dashboard de GLPI/SLA) para ingressar nela em vez de criar outra.

## Classificação de Tier (proposta)

### Projeto geral — **Tier 2** 🟠

| Pergunta | Resposta | Justificativa |
|---|---|---|
| Várias partes conversando pela rede? | Sim | Frontend, backend e API de LLM separados |
| 1 h fora do ar trava a operação? | Não | Ferramenta de apoio; o GLPI continua funcionando |
| Depende de 3+ sistemas internos? | Não | Apenas GLPI (e SSO na fase 3) |
| Centenas de usuários por dia? | Não | Dezenas, áreas de atendimento |
| Dados sensíveis de clientes? | Não | Dados operacionais de chamados internos |

1 "Sim" → Tier 2 → **2 diagramas consolidados**: Arquitetura consolidada
([01](diagramas/01-arquitetura-consolidada-glpia.puml)) + FinOps (fase 3).
O fluxo crítico ([02](diagramas/02-fluxo-critico-pergunta-ia.puml)) é complementar.

### Projeto de IA — **Tier 2 IA (Assistido)** 🟠

| Pergunta | Resposta |
|---|---|
| IA age sozinha sem confirmação? | Não — só responde e sugere filtros; o usuário aplica |
| Base de conhecimento gigante (RAG)? | Não |
| Orquestra outras automações? | Não |
| Pode alterar sistemas de produção? | Não — todas as ferramentas são somente leitura |

Exigências do Tier 2 IA: logs estruturados, gestão de custo de tokens,
versionamento de API (`/api/v1`).

## Respostas antecipadas ao questionário de SI

| Bloco | Resposta proposta |
|---|---|
| Finalidade | Dashboard de SLA e atendimento do GLPI com assistente de IA somente leitura, para áreas de service desk |
| Classificação da informação | Interno |
| Criticidade | Apoio sem impacto direto na operação |
| Dados pessoais | Sim, comuns e indiretos (nomes de requerentes/técnicos no GLPI). **Não são enviados ao LLM** — ver [ADR-0004](adr/ADR-0004-llm-recebe-somente-agregados.md): só agregados e IDs, redação de e-mail/CPF do texto do usuário com log |
| Upload/download de arquivos | Não |
| Acesso externo | Não |
| Integrações | GLPI (interna, somente leitura) e API de LLM (terceiro) via LiteLLM |

## Nomenclatura (a confirmar ao entrar na esteira)

| Item | Proposta |
|---|---|
| Nome de exibição | GLPIA |
| Repositórios formais | `ia-ti-glpia-backend`, `ia-ti-glpia-frontend` |
| `OTEL_SERVICE_NAME` | `glpia-backend-v1` |
| `sigla_area` nas specs | `S+TI` |

## Pendências

- [ ] Confirmar com a área se ranking por técnico é desejado (dado de desempenho individual).
- [ ] Confirmar versão do GLPI alvo (9.5, 10 ou 11) e perfil de usuário somente leitura para a API.
- [ ] Confirmar sigla de departamento para o nome do repositório formal.
- [ ] Este repositório é público no GitHub: ao entrar na esteira, o código passa
      para o GitLab corporativo e o repositório público deve ser arquivado ou
      tornado privado (propriedade intelectual da Positivo).
