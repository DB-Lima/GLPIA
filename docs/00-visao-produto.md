# 00 — Visão do produto

## Problema

Gestores e analistas de atendimento precisam acompanhar SLA e produtividade dos
chamados do GLPI. Hoje isso depende de relatórios nativos pouco flexíveis,
exportações manuais para planilha e filtros repetitivos. Perguntas simples
("quantos chamados do grupo N2 estouraram o SLA de solução em setembro?")
levam minutos ou exigem conhecimento do modelo de dados do GLPI.

## Proposta

**GLPIA** é um dashboard web de indicadores de SLA e atendimento do GLPI com um
assistente de IA embutido. O usuário pode:

1. Ver os indicadores principais em painéis (cards, gráficos, tabelas).
2. Filtrar por período, grupo técnico, categoria, prioridade, tipo e entidade.
3. Perguntar em linguagem natural e receber resposta em texto **e** uma
   visualização gerada a partir dos dados reais.
4. Pedir à IA que ajuste o próprio dashboard ("mostre só incidentes do N2 nos
   últimos 30 dias") — a IA devolve filtros que o front aplica.

A IA **nunca inventa números**: ela só responde com base no resultado de
ferramentas (funções) que calculam os indicadores no backend. Ver
[ADR-0003](adr/ADR-0003-ia-tool-calling-somente-leitura.md).

## Objetivo secundário: desenvolvimento guiado por IA

O projeto também é um caso de uso de **desenvolvimento assistido por IA**:

- Toda entrega nasce de uma spec (`specs/SPEC-YYYY-NNNN.yaml`) no padrão
  Spec-Driven Development, com `locked_at`, estimativas e critérios de aceite.
- Decisões ficam registradas em ADRs; arquitetura em C4-PlantUML.
- O `CLAUDE.md` e a pasta `agent_docs/` dão ao agente o contexto mínimo para
  trabalhar sem reexplicação a cada sessão.

## Público

| Persona | Necessidade principal |
|---|---|
| Coordenador(a) de atendimento | Visão de SLA e backlog por grupo, alertas de chamados em risco |
| Analista de service desk | Fila do próprio grupo, chamados próximos de vencer |
| Gestão de TI | Tendência mensal de volume, SLA e satisfação |

## Escopo do MVP

**Dentro:**
- Indicadores de [01-indicadores.md](01-indicadores.md) marcados como MVP.
- Dados vindos de um **mock** no formato do GLPI (sem instância real).
- Chat com IA em linguagem natural, somente leitura, com visualização na resposta.
- Execução local (frontend + backend + chave da API de IA via variável de ambiente).

**Fora (próximas fases):**
- Conexão com GLPI real (planejada em SPEC-2026-0006).
- Login SSO (Azure AD), RBAC por grupo/entidade.
- Deploy em QA/PRD e esteira de aprovação da TI.
- Ranking individual de técnicos (dado sensível de desempenho; ver governança).
- Qualquer escrita no GLPI (abrir, atualizar ou fechar chamados).

## Métricas de sucesso do MVP

- Uma pergunta típica de SLA respondida em menos de 10 s, com número idêntico
  ao exibido no painel para o mesmo filtro.
- 100% das respostas numéricas da IA rastreáveis a uma chamada de ferramenta.
- Troca do adapter mock pelo adapter REST sem alteração no frontend.
