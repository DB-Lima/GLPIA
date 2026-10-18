---
description: Cria a próxima spec SDD em specs/ a partir do template, para a tarefa descrita
argument-hint: <descrição curta da tarefa>
---

Crie uma nova spec para a tarefa: $ARGUMENTS

1. Liste `specs/SPEC-*.yaml`, pegue o maior número do ano corrente e some 1 (formato `SPEC-YYYY-NNNN`, 4 dígitos).
2. Copie `specs/_template.yaml` para o novo arquivo e preencha:
   - `descricao_tarefa` no formato verbo + artefato + stack + resultado esperado;
   - `tipo_tarefa` com um valor do enum;
   - 3 a 8 `criterios_aceite` binários, alinhados a `docs/` (indicadores, arquitetura, ADRs);
   - `contexto_tecnico` com dependências de outras specs e arquivos envolvidos;
   - `restricoes` relevantes (privacidade, somente leitura, sem credenciais).
3. Deixe `locked_at: null` e as estimativas como `null`: elas são do dev e vêm antes da execução.
4. Não comece a implementar. Mostre a spec e pergunte se algo deve mudar.
