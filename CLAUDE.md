# GLPIA — contexto do projeto

Dashboard de indicadores de SLA e atendimento do GLPI com assistente de IA
(somente leitura) que responde em linguagem natural e ajusta os filtros do painel.

## Stack
- Frontend: React 18 + Vite + TypeScript + Recharts (`frontend/`)
- Backend: FastAPI + Pydantic v2, Python 3.12 (`backend/`)
- IA: LiteLLM, modelo padrão Claude, tool calling somente leitura
- Dados: `GlpiPort` com adapter `mock` (MVP) e `rest` (fase 2), via `GLPI_ADAPTER`

## Como trabalhar
- Toda tarefa ≥ 15 min começa por uma spec em `specs/` — ver `agent_docs/sdd-workflow.md`
- Branch principal: `main`. Commits referenciam a spec (`Ref: SPEC-2026-NNNN`)
- Decisões de arquitetura novas viram ADR em `docs/adr/`

## Comandos (backend, rodar dentro de `backend/`; uv via `python -m uv`)
- `python -m uv sync` — cria `.venv` e instala dependências
- `python -m uv run uvicorn app.main:app --reload` — API em http://localhost:8000 (Swagger em `/docs`)
- `python -m uv run pytest --cov=app` — testes
- `python -m uv run python scripts/gerar_mock.py` — regenera o dataset fictício (seed fixa; commitar o resultado)
- Frontend: preencher quando a SPEC-2026-0004 for concluída

## Regras não negociáveis
- Fórmulas de indicadores seguem `docs/01-indicadores.md`; mudou a fórmula, mudou o doc no mesmo commit
- O LLM só recebe agregados e IDs: nunca título, descrição, nome ou e-mail (ADR-0004)
- Ferramentas da IA são somente leitura; nada de text-to-SQL (ADR-0003)
- Nenhuma credencial, token, dado real de chamado ou hostname interno no repositório (repo público)
- Configuração por variável de ambiente; `.env` nunca é commitado
- Stack fora de `docs/adr/ADR-0001` exige novo ADR

## Referências
- Visão e escopo: `docs/00-visao-produto.md`
- Indicadores: `docs/01-indicadores.md`
- Arquitetura e ferramentas da IA: `docs/02-arquitetura.md`
- Roadmap: `docs/03-roadmap.md` · Governança/Tier: `docs/04-governanca.md`
- Modelo de dados do GLPI: `agent_docs/glpi-dominio.md`
