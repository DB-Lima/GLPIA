# ADR-0005 — Monorepo no MVP

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

O fluxo automatizado de primeiro deploy da TI usa **um repositório por
componente** (sem monorepo). No MVP, porém, frontend, backend e documentação
evoluem juntos, e as specs costumam tocar mais de uma parte.

## Decisão

Manter **um único repositório** (`backend/`, `frontend/`, `docs/`, `specs/`)
enquanto o projeto for local. Ao entrar na esteira, separar em repositórios
formais no GitLab corporativo, seguindo a nomenclatura `ia-[dept]-[projeto]-[tipo]`
(ex.: `ia-ti-glpia-backend` e `ia-ti-glpia-frontend`; sigla a confirmar com a Infra).

## Consequências

- Specs e commits atômicos entre front e back no MVP.
- A separação futura exige mover histórico (`git filter-repo`) ou começar os
  repos formais do zero com o código atual; decidir no momento da migração.
