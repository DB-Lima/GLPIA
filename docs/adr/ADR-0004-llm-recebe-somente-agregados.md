# ADR-0004 — O LLM recebe somente dados agregados

- **Status:** Aceito
- **Data:** 2026-10-18

## Contexto

Chamados do GLPI contêm dados pessoais (nome e e-mail de requerente e técnico)
e texto livre que pode incluir informações sensíveis. Enviar isso a uma API
externa de LLM cria risco de LGPD e é o principal ponto de atenção da
Segurança da Informação em aplicações com IA.

## Decisão

- Ferramentas retornam ao LLM **apenas números, datas, IDs de chamado e nomes
  de grupos/categorias/entidades**.
- **Nunca** são enviados ao LLM: título, descrição, acompanhamentos, nome ou
  e-mail de pessoas.
- Antes de cada chamada externa, um filtro de redação remove padrões de e-mail
  e CPF do texto do usuário e registra em log que a redação ocorreu.
- Detalhes de chamados (título etc.) são buscados pelo frontend direto na API
  do GLPIA e exibidos só no painel.

## Consequências

- A IA não consegue responder perguntas sobre o *conteúdo* dos chamados
  ("quais chamados falam de VPN?") no MVP. Se isso for necessário, avaliar
  modelo local (modo soberano) em ADR futuro.
- Ranking por técnico individual fica fora do MVP.
