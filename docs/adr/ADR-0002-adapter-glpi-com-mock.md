# ADR-0002 — Acesso ao GLPI via adapter, começando por mock

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

Ainda não há credenciais de uma instância GLPI para o projeto, e o repositório
é público, então dados reais de chamados não podem ser versionados. Ao mesmo
tempo, o painel e a IA precisam de dados realistas para serem desenvolvidos.

## Decisão

- Definir uma interface `GlpiPort` que entrega **chamados normalizados**
  (modelo próprio, independente da versão do GLPI).
- Implementar primeiro um **adapter mock** com dados fictícios gerados por
  script com seed fixa (resultados reproduzíveis nos testes).
- Implementar depois um **adapter REST** (API `apirest.php` do GLPI 9.5/10;
  avaliar a API v2 do GLPI 11), selecionado por variável de ambiente
  `GLPI_ADAPTER=mock|rest`.

## Consequências

- O serviço de indicadores só conhece o modelo normalizado: trocar a origem
  não altera fórmulas nem frontend.
- O mock precisa cobrir casos de borda (SLA nulo, chamado sem grupo,
  pendente, reaberto, excluído) para que os testes tenham valor.
- Leitura direta do banco do GLPI fica descartada no MVP (acoplamento ao
  schema e exigência de acesso de rede ao banco).
