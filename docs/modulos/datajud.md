# Módulo: Integração DataJud (CNJ)

> Última atualização: 2026-09-15
> Camada: Backend / Frontend

---

## O que este módulo faz

Complementa a ficha de um processo já rastreado (hoje via e-SAJ/TJSP) com dados públicos da API do DataJud (CNJ) — classe, assuntos, órgão julgador, data de ajuizamento, grau, formato e movimentos públicos. É sempre uma seção **separada e somente-leitura**: nunca sobrescreve o que já vem do e-SAJ. Um job diário isolado (fora do ciclo de 10 min dos pipes) faz a coleta em lote round-robin. Ver ADR-015 para o racional completo.

Este módulo **não** descobre processos novos por nome/OAB do advogado — a API pública do DataJud não expõe partes nem advogados (Portaria CNJ nº 160/2020) e só responde consultas por número de processo já conhecido.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/core/cnj.py` | `extrair_segmento_tribunal` / `resolver_alias_datajud` — parse do número CNJ e resolução genérica do alias do índice DataJud por segmento/tribunal |
| `backend/app/services/datajud.py` | `consultar_processo` — cliente HTTP (httpx) da API pública do DataJud, timeout 10s, nunca lança |
| `backend/app/schemas/datajud_raw.py` | `DatajudProcessoRaw` e submodelos — schema Pydantic do `_source` de um hit (`extra="ignore"`) |
| `backend/app/models/processo_datajud.py` | `ProcessoDatajud` — tabela complementar 1:1 com `Processo` |
| `backend/app/services/datajud_jobs.py` | `job_datajud_diario` — job de sistema, lote round-robin, isolamento de falha por processo |
| `backend/app/models/job_log.py` | `JOB_TIPO_DATAJUD` |
| `backend/app/core/scheduler.py` | Registro do cron (`JOB_ID_DATAJUD_DIARIO`, 3h `America/Sao_Paulo`) |
| `backend/app/schemas/processo.py` | `ProcessoDatajudPublicSchema` + campo `datajud` em `ProcessoDetalheSchema` |
| `backend/app/services/painel.py` | `datajud_para_publico`; `buscar_processo_detalhe` carrega o `ProcessoDatajud` do processo |
| `backend/app/core/email_provider.py` | `detectar_provedor_por_dominio` — detecção de Gmail/Outlook por MX (parte da mesma etapa, ver `/docs/modulos/credenciais-esaj-email.md`) |
| `backend/app/db/migrations/versions/e5b3f7a2c916_cria_processos_datajud.py` | Migration da tabela `processos_datajud` |
| `frontend/src/features/processos/ProcessoDatajudSecao.tsx` | Seção somente-leitura na ficha do processo |
| `frontend/src/features/processos/processos.types.ts` | `ProcessoDatajudPublica`, `DatajudAssuntoPublica`, `DatajudMovimentoPublica` |

---

## Endpoints

Nenhum endpoint dedicado — os dados do DataJud saem embutidos em `GET /processos/{id}` (campo `datajud`, ver `/docs/modulos/processos.md`). Não existe endpoint para disparar uma consulta manual ao DataJud (fora de escopo desta etapa, ver ADR-015).

---

## Jobs e schedulers

| Job | Frequência | Descrição |
|---|---|---|
| `job_datajud_diario` | Cron, 3h da manhã (`America/Sao_Paulo`) | Job de **sistema** (não por advogado): seleciona um lote round-robin (`DATAJUD_LOTE=300`) priorizando processos nunca consultados, depois os mais atrasados; consulta o DataJud e faz upsert em `ProcessoDatajud`; grava `JobLog(tipo=datajud)` por processo |

`id` fixo (`datajud_diario`), `replace_existing=True`, `max_instances=1`, `coalesce=True` — mesmo padrão dos outros jobs (`/docs/modulos/scheduler.md`).

### Fluxo do job

```
job_datajud_diario
  → _selecionar_lote_datajud (round-robin: nunca consultado > mais atrasado)
  → para cada processo (isolado em try/except):
      resolver_alias_datajud(nu_processo)
        None → JobLog status=skip, motivo=tribunal_nao_mapeado (não é erro)
        alias → datajud.consultar_processo (httpx, timeout 10s)
          None (não achou / erro de rede/HTTP) → upsert encontrado=false
          DatajudProcessoRaw → upsert encontrado=true + campos
      → JobLog status=sucesso | falha
  → intervalo pequeno entre chamadas (INTERVALO_ENTRE_CONSULTAS_SEGUNDOS)
```

---

## Padrões seguidos neste módulo

- **Nunca sobrescreve o e-SAJ:** `ProcessoDatajud` é uma tabela separada, 1:1 com `Processo` — os campos que já vêm do e-SAJ (`de_classe`, `de_assunto`, `foro`, `vara`...) nunca são tocados por este módulo
- **Isolamento por processo:** `_processar_processo` roda em `try/except` próprio — falha em um processo nunca impede os demais no mesmo lote (`security.mdc` §8), igual ao padrão do `job_ciclo_dez_minutos`
- **Nunca lança para o chamador:** `datajud.consultar_processo` devolve `None` em qualquer falha (rede, HTTP, JSON malformado, validação Pydantic) — nunca propaga exceção
- **Timeout curto:** 10s por requisição HTTP (`security.mdc` §12) — API pública de terceiro, não pode travar o job
- **Log sem payload:** qualquer log de erro do cliente/job usa só o tipo do problema (status HTTP, nome da exceção) — nunca o corpo da resposta
- **Chave de API em variável de ambiente:** `DATAJUD_API_KEY`, mesmo sendo uma chave pública compartilhada da wiki do CNJ — nunca hardcoded (o CNJ já trocou essa chave antes). Sem a chave, `job_datajud_diario` loga uma vez e sai — não marca `encontrado=false` em lote
- **Alias por segmento/tribunal, não hardcode de TJSP:** `resolver_alias_datajud` cobre Justiça Estadual (27 UFs), TRFs (1–6), TRTs (1–24) e STF/STJ/TST; tribunal fora dessa tabela devolve `None` (skip, não erro) — ver ADR-015
- **Resposta:** `ProcessoDatajudPublicSchema` — nunca o model ORM diretamente
- **Ownership:** `buscar_processo_detalhe` só carrega `ProcessoDatajud` depois de validar que o `Processo` pertence a `current_user.id` — o `processo_id` usado na segunda query não vem do cliente, vem do registro já validado
- **Round-robin, não full scan:** mesmo espírito do throttle de movimentações do CPO (ADR-012) — evita martelar a chave pública compartilhada a cada execução

---

## Modelo de dados relacionado

```python
class ProcessoDatajud(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processos_datajud"

    processo_id: Mapped[uuid.UUID]      # FK processos.id, unique+index, ON DELETE CASCADE
    tribunal_alias: Mapped[str]         # "tjsp", "trf3"... (resolver_alias_datajud)
    classe_codigo: Mapped[str | None]
    classe_nome: Mapped[str | None]
    assuntos: Mapped[list[dict] | None]      # JSONB [{codigo, nome}, ...]
    orgao_julgador: Mapped[str | None]
    data_ajuizamento: Mapped[datetime | None]
    grau: Mapped[str | None]
    formato: Mapped[str | None]
    movimentos: Mapped[list[dict] | None]    # JSONB [{codigo, nome, data_hora}, ...]
    encontrado: Mapped[bool]            # False = consultado, mas o DataJud não tem (ainda)
    ultima_consulta_em: Mapped[datetime]
```

Uma linha por `Processo` (1:1). `encontrado=False` é um estado normal (defasagem de replicação do DataJud), nunca tratado como erro na UI.

Migration: `e5b3f7a2c916_cria_processos_datajud.py` (head anterior: `d4a8c2e1f9b0`).

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| Painel de Processos | `buscar_processo_detalhe` carrega `ProcessoDatajud` do mesmo processo e expõe no `ProcessoDetalheSchema.datajud` |
| Scheduler | `job_datajud_diario` é registrado e controlado pelo mesmo `AsyncIOScheduler` (`scheduler_enabled`) |
| Migrations / camada de dados | Tabela `processos_datajud`, sessão async, Alembic |

Nenhum módulo depende deste além do painel — é estritamente aditivo.

---

## O que NÃO fazer aqui

- ❌ Não usar o DataJud para descobrir processos por nome/OAB do advogado — a API pública não expõe essa informação (Portaria CNJ 160/2020) e não é esse o propósito deste módulo
- ❌ Não sobrescrever nenhum campo de `Processo` com dado do DataJud — sempre uma tabela/seção separada
- ❌ Não rodar o complemento no ciclo de 10 min dos pipes e-SAJ — é um job diário, de sistema, isolado de propósito (ADR-015)
- ❌ Não hardcodar o alias `tjsp` — usar sempre `resolver_alias_datajud`, mesmo que hoje só o e-SAJ/TJSP esteja em produção
- ❌ Não tratar tribunal não mapeado (`resolver_alias_datajud` devolve `None`) como erro — é "ainda não suportado", grava `JobLog status=skip`
- ❌ Não deixar uma falha de rede/HTTP do DataJud propagar para o job inteiro — sempre isolado por processo
- ❌ Não logar o payload da resposta do DataJud em caso de erro — só o tipo do problema
- ❌ Não hardcodar `DATAJUD_API_KEY` no código — variável de ambiente, mesmo sendo uma chave pública compartilhada
- ❌ Não varrer o lote do job diário com `DATAJUD_API_KEY` vazio — isso gravaria `encontrado=false` e atrasaria a consulta real
- ❌ Não criar endpoint para "atualizar dados públicos" manualmente nesta etapa — só o job diário automático (fora de escopo, ver ADR-015)

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-09-06 | Implementação inicial (Etapa 9): `app/core/cnj.py`, cliente `app/services/datajud.py`, model `ProcessoDatajud` + migration, `job_datajud_diario`, exposição em `ProcessoDetalheSchema.datajud`, seção somente-leitura na ficha do processo (ADR-015) |
| 2026-09-15 | `job_datajud_diario` não varre o lote quando `DATAJUD_API_KEY` está vazio |
