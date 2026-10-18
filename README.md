# GLPIA

Dashboard de indicadores de SLA e atendimento do GLPI com um assistente de IA
que responde perguntas em linguagem natural e ajusta os filtros do painel.

> **Status:** MVP funcional com dados fictícios (SPECs 0001 a 0005). A conexão
> com um GLPI real é a próxima fase (SPEC-2026-0006).

## Funcionalidades

- **Painel:** volume de chamados, backlog por idade, cumprimento de SLA de
  atendimento (TTO) e de solução (TTR), chamados com SLA vencido ou em risco,
  tempos médios e distribuição por categoria, grupo, prioridade, tipo e entidade.
- **Filtros na URL:** período, grupo técnico, categoria, prioridade, tipo e
  entidade. Recarregar ou compartilhar o link mantém o mesmo recorte.
- **Chat com IA:** "qual o SLA de solução do N2 em setembro?" → resposta em
  texto, gráfico, botão para aplicar o recorte ao painel e "Como calculei"
  (quais ferramentas e argumentos foram usados).
- **IA confiável por construção:** o modelo só acessa dados por ferramentas
  somente leitura, recebe apenas números agregados (nunca títulos, nomes ou
  e-mails) e os gráficos são montados pelo backend a partir do resultado real.

## Pré-requisitos

- Python 3.12+ e [uv](https://docs.astral.sh/uv/) (`pip install uv`; se o comando `uv`
  não for encontrado, use `python -m uv` no lugar)
- Node.js 20+ e npm
- Para o chat: uma chave da API da Anthropic com créditos (o painel funciona sem ela)

## Como rodar

```bash
git clone https://github.com/DB-Lima/GLPIA.git
cd GLPIA
cp .env.example .env   # preencha ANTHROPIC_API_KEY para usar o chat
```

Backend (terminal 1):

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

API em http://localhost:8000 · documentação interativa em http://localhost:8000/docs

Frontend (terminal 2):

```bash
cd frontend
npm install
npm run dev
```

Painel em http://localhost:5173 (o Vite encaminha `/api` para o backend).

## Testes

```bash
cd backend && uv run pytest --cov=app    # 82 testes, cobertura ~97%
cd frontend && npm test && npm run build # testes de filtros + checagem de tipos
```

Os testes do chat usam um LLM simulado e não consomem a API.

## Dados

O MVP usa 5.000 chamados **fictícios** no formato das tabelas do GLPI
([backend/data/mock/glpi_mock.json](backend/data/mock/glpi_mock.json)), gerados
de forma determinística por `backend/scripts/gerar_mock.py` (seed 42, data de
referência 15/10/2026). Nenhum dado real é versionado.

## Configuração (`.env`)

| Variável | Padrão | Uso |
|---|---|---|
| `GLPI_ADAPTER` | `mock` | Origem dos dados (`rest` na fase 2) |
| `LLM_MODEL` | `anthropic/claude-opus-5-5` | Modelo principal, no formato do LiteLLM |
| `LLM_FALLBACK_MODEL` | vazio | Modelo usado em timeout, 429 ou 5xx do principal |
| `LLM_TIMEOUT_SEGUNDOS` | `30` | Timeout por chamada ao modelo |
| `ANTHROPIC_API_KEY` | — | Chave do provedor (nunca commitar) |

## Limitações conhecidas

- O chat foi validado ponta a ponta com LLM simulado e a requisição real chegou à
  API da Anthropic, mas a conversa completa com o modelo real ainda não foi
  testada (conta sem créditos). Critério pendente da SPEC-2026-0005.
- Os prazos de SLA no mock contam relógio corrido; o GLPI real desconta o
  calendário de atendimento.
- Sem autenticação: uso local apenas. SSO e RBAC estão na fase 3 do
  [roadmap](docs/03-roadmap.md).

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
   aceite verificáveis, escrita e travada (`locked_at`) **antes** da execução.
2. O agente (Claude Code) lê o `CLAUDE.md` e os arquivos de `agent_docs/` para
   ter o contexto do projeto sem reexplicação.
3. Decisões viram ADRs; os critérios de aceite são conferidos um a um com
   evidência (teste, comando ou verificação no navegador) antes do commit.

Comandos do projeto no Claude Code: `/nova-spec` e `/travar-spec`.

## Estrutura

```
backend/    FastAPI: domínio (fórmulas), serviços, adapters GLPI, agente de IA, testes
frontend/   React + Vite: painel, filtros, chat
docs/       visão, indicadores, arquitetura, ADRs, diagramas
specs/      specs SDD de cada entrega
agent_docs/ contexto detalhado para o agente de IA
```

## Stack

React 18 + Vite + TypeScript + Recharts · FastAPI + Pydantic (Python 3.12) · LiteLLM + Claude
