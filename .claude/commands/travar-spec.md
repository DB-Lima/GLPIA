---
description: Trava uma spec (preenche locked_at) e inicia a execução
argument-hint: <SPEC-YYYY-NNNN>
---

Trave e execute a spec $ARGUMENTS.

1. Abra `specs/$ARGUMENTS.yaml`. Se `locked_at` já estiver preenchido, pare e avise.
2. Confira se os campos obrigatórios estão preenchidos: estimativas Jr/Pleno/Sr, 3 a 8 critérios de aceite, `tipo_tarefa` válido. Se faltar algo, pare e peça ao usuário.
3. Preencha `locked_at` com a data e hora atuais no formato `YYYY-MM-DDTHH:MM:SS-03:00` e remova o comentário de RASCUNHO.
4. Faça commit só da spec: `spec: trava $ARGUMENTS`.
5. Execute a tarefa seguindo a spec, `CLAUDE.md` e os documentos citados em `contexto_tecnico`.
6. Ao final, liste cada critério de aceite com ✅ ou ❌ e a evidência (comando, teste ou arquivo).
