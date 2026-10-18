# ADR-0001 — Stack React + Vite e FastAPI

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

O MVP precisa de um painel interativo e de um backend que fale com o GLPI e
com uma API de LLM. A stack precisa estar na lista aprovada pela Arquitetura
Corporativa para que o projeto possa seguir para a esteira sem exceção formal.

## Decisão

- Frontend: **React 18 + Vite + TypeScript**, gráficos com **Recharts**.
- Backend: **FastAPI (Python 3.12)** com Pydantic v2.
- Python é preferido para a parte de IA (ecossistema LiteLLM/LangGraph/OpenLIT).

## Alternativas consideradas

| Opção | Motivo de não escolher |
|---|---|
| Streamlit | Mais rápido para protótipo, mas fora da stack aprovada e limitado para UI de chat + painel |
| Metabase | Aprovado para BI self-service, mas não permite o chat com IA controlando filtros |
| Node/Express no backend | Aprovado, mas Python é preferido em apps de IA |

## Consequências

- Dois processos para rodar localmente (Vite dev server e Uvicorn).
- Build do front vira estático servido por nginx (imagem UBI) quando houver deploy.
