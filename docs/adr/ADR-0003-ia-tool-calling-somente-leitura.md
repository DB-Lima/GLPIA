# ADR-0003 — IA via LiteLLM com tool calling somente leitura

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

O usuário quer perguntar em linguagem natural e receber dados corretos. LLMs
alucinam números quando respondem "de memória" e geram consultas inseguras
quando recebem liberdade para montar SQL. A stack corporativa exige um router
de LLM para permitir troca de provedor.

## Decisão

- Usar **LiteLLM** como camada de acesso ao LLM, com **Claude** como modelo
  padrão (configurável por `LLM_MODEL`). Provedor de fallback configurável por
  `LLM_FALLBACK_MODEL`.
- A IA só acessa dados por **ferramentas pré-definidas** (ver
  [02-arquitetura.md](../02-arquitetura.md)), todas **somente leitura** e com
  parâmetros validados.
- A resposta final segue um **schema JSON** (resposta, visualização, filtros
  sugeridos, rastreio). Saída fora do schema é rejeitada e reprocessada uma vez.
- Prompts ficam em YAML versionado em `backend/app/ai/prompts/`.

## Alternativas consideradas

| Opção | Motivo de não escolher |
|---|---|
| Text-to-SQL | Risco de consultas destrutivas ou caras, expõe schema e dados brutos |
| SDK da Anthropic direto | Mais simples, mas fora do padrão de router corporativo |
| LangGraph já no MVP | Útil quando houver estado e múltiplos passos; para o MVP o loop de tool calling basta. Reavaliar na fase 3 |

## Consequências

- Toda resposta numérica é rastreável a uma chamada de ferramenta.
- Perguntas fora do catálogo de ferramentas recebem resposta de "não sei"
  em vez de um número inventado — esperado e desejável.
- Classificação proposta: **Tier 2 IA (Assistido)** — ver [04-governanca.md](../04-governanca.md).
