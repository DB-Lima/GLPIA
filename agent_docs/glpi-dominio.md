# Domínio GLPI — referência para o agente

Resumo do que o GLPIA usa do GLPI. Nomes de campos seguem a tabela
`glpi_tickets` (GLPI 10). **Confirmar na instância real** antes da SPEC-2026-0006:
versões diferentes mudam nomes e os IDs de *search options* da API.

## Chamado (`glpi_tickets`)

| Campo GLPI | Tipo | Uso no GLPIA |
|---|---|---|
| `id` | int | identificador |
| `entities_id` | int | filtro entidade |
| `name` | texto | título — **só no painel, nunca ao LLM** |
| `content` | texto | descrição — **não usado** |
| `date` | datetime | abertura |
| `takeintoaccountdate` | datetime | quando foi assumido (TTO) |
| `solvedate` | datetime | solução |
| `closedate` | datetime | fechamento |
| `status` | int | ver tabela abaixo |
| `type` | int | 1 = incidente, 2 = requisição |
| `priority` | int | 1 (muito baixa) a 6 (crítica) |
| `urgency`, `impact` | int | 1 a 5 (pós-MVP) |
| `itilcategories_id` | int | categoria |
| `time_to_own` | datetime | prazo de SLA de atendimento (TTO) |
| `time_to_resolve` | datetime | prazo de SLA de solução (TTR) |
| `internal_time_to_own`, `internal_time_to_resolve` | datetime | OLA interno (pós-MVP) |
| `slas_id_tto`, `slas_id_ttr` | int | SLA aplicado |
| `takeintoaccount_delay_stat` | int (s) | tempo até assumir, em horário útil |
| `solve_delay_stat` | int (s) | tempo até solucionar, em horário útil |
| `waiting_duration` | int (s) | tempo em pendente |
| `is_deleted` | bool | excluídos nunca entram nos indicadores |

### Status

| Código | Nome | Aberto? |
|---|---|---|
| 1 | Novo | sim |
| 2 | Em atendimento (atribuído) | sim |
| 3 | Em atendimento (planejado) | sim |
| 4 | Pendente | sim |
| 5 | Solucionado | não |
| 6 | Fechado | não |

## Relações

| Tabela | Uso |
|---|---|
| `glpi_groups_tickets` | `type = 2` → grupo técnico atribuído (pode haver vários) |
| `glpi_tickets_users` | requerente/técnico — **não usado no MVP** (PII) |
| `glpi_itilcategories` | nome e hierarquia (`completename`) da categoria |
| `glpi_entities` | nome da entidade |
| `glpi_ticketsatisfactions` | `satisfaction` 0–5, `date_answered` (IND-08) |

## Modelo normalizado (contrato do `GlpiPort`)

```python
class Chamado(BaseModel):
    id: int
    entidade: str
    titulo: str                # nunca serializado para o LLM
    aberto_em: datetime
    assumido_em: datetime | None
    solucionado_em: datetime | None
    fechado_em: datetime | None
    status: StatusChamado      # enum 1..6
    tipo: Literal["incidente", "requisicao"]
    prioridade: int            # 1..6
    categoria: str | None      # completename
    grupos_tecnicos: list[str]
    prazo_tto: datetime | None
    prazo_ttr: datetime | None
    segundos_ate_assumir: int | None
    segundos_ate_solucionar: int | None
    excluido: bool
```

## API REST (fase 2)

- Sessão: `GET /apirest.php/initSession` com headers `App-Token` e
  `Authorization: user_token <token>` → `session_token`; encerrar com `killSession`.
- Listagem: `GET /apirest.php/search/Ticket` com `criteria[]`, `forcedisplay[]`
  e `range=0-999` (paginação via header `Content-Range`).
- IDs de campo para `forcedisplay`: obter com `GET /apirest.php/listSearchOptions/Ticket`.
- GLPI 11 traz uma API v2 (`/api.php/v2`) com OAuth2 — avaliar se a instância for 11.
