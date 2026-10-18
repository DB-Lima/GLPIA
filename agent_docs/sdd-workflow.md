# Fluxo de trabalho com specs (SDD)

Toda tarefa de 15 min ou mais nasce de uma spec em `specs/`.

## Ciclo

1. **Criar** — copiar `specs/_template.yaml` para o próximo `SPEC-2026-NNNN.yaml`
   (ou usar `/nova-spec`). Nunca reutilizar um ID.
2. **Preencher antes de executar** — descrição (verbo + artefato + stack +
   resultado), 3 a 8 critérios de aceite binários, estimativas Jr/Pleno/Sr
   **sem IA**, contexto técnico e restrições.
3. **Travar** — no momento de entregar a tarefa ao agente, preencher
   `locked_at` com data/hora atual em `-03:00` (ou usar `/travar-spec`) e
   commitar a spec antes do código.
4. **Executar** — o agente trabalha com a spec como contexto da tarefa.
5. **Verificar** — cada critério de aceite vira item de checklist no PR/MR
   (`Ref: SPEC-2026-NNNN`). Critério não atendido = tarefa não concluída.
6. **Mudança de escopo depois do lock** — nova spec com novo ID e
   `spec_version: 1`; a antiga fica como está.

## Regras

- `tipo_tarefa` só aceita: `codigo`, `analise`, `documento`, `relatorio`,
  `email`, `pesquisa`, `reuniao`, `apresentacao`, `outro`.
- `sigla_area`: `S+TI`.
- Repositório público: `usuario`/`email` ficam como `<email-corporativo>`;
  o e-mail real vai só no registro de KPI.
- Critério com "parece", "limpo", "bom" não é critério.
