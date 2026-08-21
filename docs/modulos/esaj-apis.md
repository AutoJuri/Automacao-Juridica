# Módulo: Contrato das APIs internas do e-SAJ (TJSP)

> Última atualização: 2026-08-21
> Camada: Backend / Scraping

---

## O que este módulo faz

Registra o **contrato observado** das APIs internas do e-SAJ (TJSP) e o mapeamento campo → coluna dos pipes. Fonte original: capturas do lab em `scripts/esaj/results/` (gitignorado). Em 2026-08-20 o ciclo real (`coleta_esaj.executar_ciclo_usuario`) foi rodado contra uma sessão `ativo` e cruzado com o painel do advogado — os achados dessa validação estão na seção correspondente, sem payload cru no Git.

Fonte das capturas de lab: 2026-07-02 (detalhe CPO) e 2026-07-03 (JSON `tarefas-adv/api`). Os JSON crus **não** entram no Git: têm nome de parte, OAB e número de processo.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `scripts/esaj/results/*.json` | Capturas locais (gitignoradas) — fonte deste contrato |
| `backend/app/models/processo.py` | Destino do GET `/api/processos` (upsert) |
| `backend/app/models/intimacao.py` | Destino do GET `/api/intimacoes` |
| `backend/app/models/audiencia.py` | Destino do GET `/api/audiencias` — `id_esaj` **composto no ETL** (a API não manda `id`) |
| `backend/app/models/movimentacao.py` | Destino previsto do HTML CPO — **não vem do JSON de processos** |
| `backend/app/services/auth_esaj.py` | Warm-up das 4 telas `tarefas-adv` que habilitam essas APIs |
| `backend/app/services/esaj_http.py` | Client httpx autenticado + detecção de sessão inválida + `validar_itens` (item a item, sem logar payload) |
| `backend/app/schemas/esaj_raw.py` | Schemas Pydantic do payload bruto (`IntimacaoRaw`, `AudienciaRaw`, `ProcessoRaw`, `ParteRaw`) |
| `backend/app/etl/etl.py` | Normalização (timezone, id composto de audiência, truncate de `titulo`/`local`/`id_esaj` em 255, bruto → campos do model) |
| `backend/app/etl/diff.py` | Diff contra o banco, upsert de `Processo`, geração de `Notification` e `is_new=False` após notificar |
| `backend/app/services/pipes/pipe_intimacoes.py`, `pipe_audiencias.py`, `pipe_processos.py` | Coleta (fetch) de cada API |
| `backend/app/services/coleta_esaj.py` | Orquestrador do ciclo por advogado (`executar_ciclo_usuario`) e de todos (`executar_ciclo_todos_usuarios`) |
| `backend/scripts/disparar_coleta.py` / `verificar_coleta.py` | Smoke manual (não é pytest): dispara o ciclo e imprime relatório sanitizado |

Pipes, schemas do bruto e orquestrador implementados na Etapa 7 — intimações, audiências e upsert de ficha de processos. Validado ao vivo em 2026-08-20 (primeiro ciclo persiste; segundo ciclo diff = 0). `pipe_peticoes.py` continua stub (fora do ciclo, ADR-010) e o pipe de movimentações via CPO continua sem fixture boa. Na Etapa 8 o APScheduler passou a chamar `executar_ciclo_usuario` a cada 10 minutos (via `scheduler_jobs.job_ciclo_dez_minutos`, ver `/docs/modulos/scheduler.md`) e o HTTP 429 do e-SAJ ganhou tratamento próprio (`EsajRateLimitError` → `bloqueado` com backoff, sem invalidar o cookie).

---

## Endpoints (e-SAJ, não a nossa API)

Auth: cookie de sessão do advogado (`JSESSIONID` de `/tarefas-adv` + `CASTGC`), já persistido criptografado em `TribunalSession`. Base: `https://esaj.tjsp.jus.br`.

| Método | Rota observada | O que devolve | No ciclo de 10 min? |
|---|---|---|---|
| GET | `/tarefas-adv/api/intimacoes` | Array de intimações da carteira | Sim → `intimacoes` |
| GET | `/tarefas-adv/api/audiencias` | Array de audiências da carteira | Sim → `audiencias` |
| GET | `/tarefas-adv/api/processos?cdsProcesso=` | Array de fichas; **exige** um ou mais `cdsProcesso` | Sim → `processos` upsert |
| GET | `/tarefas-adv/api/peticoes?situacao=AGUARDANDO_ASSINATURA` | Rascunhos pendentes de assinatura | **Não** (ver petições) |
| GET | `/cpopg/show.do?processo.codigo=` | HTML da capa + movimentações | Sim, **só** com parser + fixture de `movimentacoes` preenchido |
| GET | `/cpopg/abrirPastaDigitalIntegracao.do?cdProcesso=` | Pasta digital (URL já vem no JSON de processos) | Fora do MVP (PDF) |

Envelope das capturas JSON do lab (wrapper nosso, não do e-SAJ): `endpoint`, `status_code`, `fetched_at`, `final_url`, `ok`, `data`, `error`, `auth_redirect`. O contrato abaixo descreve só `data`.

Resposta `data`: **array na raiz** (não `{ items: [] }`). Sem paginação observada nessas capturas.

---

## Fluxo: de onde sai, onde cai

```mermaid
flowchart LR
  cookie["TribunalSession cookie ativo"] --> intimacoesApi["GET intimacoes"]
  cookie --> audienciasApi["GET audiencias"]
  cookie --> processosApi["GET processos?cdsProcesso"]
  cookie --> cpoHtml["GET cpopg/show.do"]
  intimacoesApi --> tabInt["intimacoes"]
  audienciasApi --> tabAud["audiencias"]
  intimacoesApi --> ids["unio cdProcesso"]
  audienciasApi --> ids
  persistidos["processos ja no banco"] --> ids
  ids --> processosApi
  processosApi --> tabProc["processos upsert"]
  tabInt --> joinProc["processo_id via cd_processo"]
  tabAud --> joinProc
  joinProc --> tabProc
  cpoHtml --> tabMov["movimentacoes append"]
  peticoesApi["GET peticoes"] --> backlog["fora do ciclo MVP"]
```

**Versionamento do MVP** (já no schema — não é tabela de versões):

- `processos`: 1 linha atual por `(user_id, cd_processo)` — upsert da ficha.
- `intimacoes` / `audiencias` / `movimentacoes`: evento append-only com unique; o diff notifica só o que é **novo**.

**Auto-relação processo → processo** (apenso, recurso): **não aparece** nesses JSON. Não modelar até o payload exigir e o painel pedir.

---

## 1. Intimações — `GET /tarefas-adv/api/intimacoes`

Tela no lab: `/tarefas-adv/intimacoes` (warm-up). **No painel do advogado (validação 2026-08-20)** a lista equivalente é o menu **Manifestações / ciência** — a rota HTML `/tarefas-adv/intimacoes` pode vir vazia e mesmo assim a API JSON devolve os itens. O rótulo de produto no nosso painel deve seguir “Manifestações / ciência”, não “Intimações” isolado. Sem query na captura.

Exemplo sanitizado de um item de `data`:

```json
{
  "id": "cdProcesso=1A0000XXXX0000,nuSeqIntimacao=10,nuSeqProcessoMv=19,oab=XXXXXXUF",
  "titulo": "Mero expediente",
  "descricao": "Texto da intimação...",
  "cdProcesso": "1A0000XXXX0000",
  "instancia": "PG",
  "dataMovimentacao": "2026-06-30T11:14:06",
  "ciencia": false
}
```

| Campo API | Destino | Notas |
|---|---|---|
| `id` | `intimacoes.id_esaj` | Composto estável na captura. **Contém OAB** — persiste como chave, **nunca logar**. Cortado em 255 no ETL (`ID_ESAJ_MAX`) |
| `titulo` | `intimacoes.titulo` | Cortado em 255 no ETL (`TITULO_MAX`) |
| `descricao` | `intimacoes.descricao` | Texto longo; sanitizar no front (XSS) |
| `cdProcesso` | join → `processos.cd_processo` | `processo_id` nullable até a ficha existir |
| `instancia` | `intimacoes.instancia` | Ex.: `PG` |
| `dataMovimentacao` | `intimacoes.data_movimentacao` | Sem timezone — ver padrão abaixo |
| `ciencia` | `intimacoes.ciencia` | `false` = ainda sem ciência no e-SAJ |

Unique já no banco: `(user_id, id_esaj)`.

---

## 2. Audiências — `GET /tarefas-adv/api/audiencias`

Tela: `/tarefas-adv/audiencias`. Sem query na captura. **Não há campo `id`.**

Exemplo sanitizado:

```json
{
  "dataMovimentacao": "2026-05-25T17:30:29",
  "dataAudiencia": "2026-07-21T16:00:00",
  "situacao": "Pendente",
  "titulo": "Instrução, Debates e Julgamento",
  "local": "Sala de Audiências",
  "cdProcesso": "1A0000XXXX0000"
}
```

| Campo API | Destino | Notas |
|---|---|---|
| `titulo` | `audiencias.titulo` | Entra no `id_esaj` composto; cortado em 255 no ETL (`TITULO_MAX`) |
| `local` | `audiencias.local` | Fora da chave (mudança de sala não cria evento novo); cortado em 255 (`LOCAL_MAX`) |
| `dataAudiencia` | `audiencias.data_audiencia` | Entra no `id_esaj` composto |
| `cdProcesso` | join → `processos` | Entra no `id_esaj` composto |
| `situacao` | **não persiste** | MVP: “Pendente” = `data_audiencia >= agora` |
| `dataMovimentacao` | **não persiste** | Data do andamento que gerou a audiência, não a sessão |

**`id_esaj` (ADR-010):** o ETL monta um id canônico estável e grava em `audiencias.id_esaj`:

```text
cdProcesso={cd}|dataAudiencia={iso}|titulo={titulo}
```

Unique continua `(user_id, id_esaj)`. Não usar UUID por captura (o diff duplicaria a cada ciclo). Se o composto passar de 255, o ETL trunca **só o título** na chave (prefixo `cdProcesso|dataAudiencia` permanece). Se o e-SAJ mudar só o título da mesma sessão, pode nascer um evento “novo” e um órfão — aceitável no MVP.

---

## 3. Processos (ficha) — `GET /tarefas-adv/api/processos`

Tela: home `tarefas-adv`. Query **obrigatória**: um ou mais `cdsProcesso` repetidos.

```
GET /tarefas-adv/api/processos?cdsProcesso=AAA&cdsProcesso=BBB
```

Não é “lista da carteira”. A captura pediu 4 códigos e **devolveu 3** (HTTP 200, item omitido). O pipe deve tratar código ausente sem falhar o lote.

Exemplo sanitizado de um item:

```json
{
  "cdProcesso": "1A0000XXXX0000",
  "nuProcesso": "00000000000000000000",
  "deClasse": "Procedimento Comum Cível",
  "deAssunto": "Assunto do processo",
  "instancia": "PG",
  "parteAtiva": { "nome": "Parte Ativa", "representada": true },
  "partePassiva": { "nome": "Parte Passiva", "representada": false },
  "urlCpo": "https://esaj.tjsp.jus.br/cpopg/show.do?processo.codigo=1A0000XXXX0000",
  "urlPasta": "https://esaj.tjsp.jus.br/cpopg/abrirPastaDigitalIntegracao.do?cdProcesso=1A0000XXXX0000&modoServico=false"
}
```

| Campo API | Destino | Notas |
|---|---|---|
| `cdProcesso` | `processos.cd_processo` | Unique com `user_id` |
| `nuProcesso` | `processos.nu_processo` | Dígitos sem máscara na API |
| `deClasse` | `processos.de_classe` | |
| `deAssunto` | `processos.de_assunto` | |
| `instancia` | `processos.instancia` | |
| `parteAtiva` | `processos.parte_ativa` JSONB | Só `nome` + `representada` na captura; PRD cita `nomeSocial` — ausente |
| `partePassiva` | `processos.parte_passiva` JSONB | `nome` pode faltar (petição aninhada veio só `representada`) |
| `urlCpo` | `processos.url_cpo` | |
| `urlPasta` | `processos.url_pasta` | |
| — | `processos.status` | **Não veio** nesta API |

**Não traz movimentações.** Histórico = HTML do CPO, só depois da fixture boa (ADR-010).

**De onde saem os `cdsProcesso` (ADR-010):**

- **Ciclo de 10 min:** união de `cdProcesso` de intimações + audiências + linhas **já** em `processos` daquele advogado. Código pedido que não voltar no 200: `job_log` skip, não derruba o lote.
- **Carteira completa** (“todos os processos” do PRD): importação à parte, quando o Network da home `tarefas-adv` revelar outra lista. Não bloqueia intimação/audiência/ficha. Processo quieto ainda não persistido fica de fora até essa importação.

---

## 4. Petições — `GET /tarefas-adv/api/peticoes`

Captura com `?situacao=AGUARDANDO_ASSINATURA`. **Não é** andamento do processo: é rascunho no peticionamento, com `cdProtocolo` UUID e `urlPeticionamento`. O objeto `processo` aninhado tem `nuProcesso` e partes — **sem** `cdProcesso`.

No painel do advogado isso é o menu **Assinar e enviar** / cards **Assinatura pendente** (ex.: “Petição Intermediária - Digitalização”). Confirmado na validação 2026-08-20 — não entra no ciclo de monitoramento.

Não há tabela `peticoes`. **Fora do ciclo de 10 minutos** (ADR-010). O PRD citava `pipe_peticoes.py`; o JSON real não é andamento nos autos. Petição que aparecer no CPO (quando o parser existir) cai em `movimentacoes`.

Se o produto pedir um card “aguardando assinatura” depois: unique `cdProtocolo` por advogado, tabela própria — não misturar com `movimentacoes`. Outros valores de `situacao` não foram capturados.

---

## 5. Detalhe CPO — `GET /cpopg/show.do?processo.codigo=`

HTML parseado no lab (não é JSON do `tarefas-adv`). Duas capturas úteis:

1. Processo acessível: `dados_gerais` preenchido; `movimentacoes` veio **`[]`**; `peticoes_diversas` é lista `{ data, tipo }` — **a primeira linha é cabeçalho da tabela** (`Data` / `Tipo`).
2. Processo em segredo: `requer_senha_processo: true`, `ok: false`; mesmo assim veio capa parcial; `partes` / `peticoes_diversas` saíram poluídas com linhas de inquérito.

Campos extras da capa (foro, vara, juiz, área, distribuição, controle, delegacia): **não** estão em `Processos`. Ignorar no MVP; o card usa classe/assunto/partes do GET `/api/processos`.

| Campo parseado | Destino previsto | Notas |
|---|---|---|
| `dados_gerais.numero` | `nu_processo` (máscara CNJ) | Às vezes o topo do JSON lab vem vazio e o número só está aqui |
| `movimentacoes[]` | `movimentacoes` | **Vazio nas capturas atuais.** Pipe só depois de 1 fixture com array preenchido; ignorar 1ª linha se `data`/`tipo` forem cabeçalho (`Data`, `Tipo`, `Documento`, `Número`) |
| `peticoes_diversas[]` | não persistir | Header-as-row; **não** usar como substituto de movimentação |
| `bloqueio.requer_senha_processo` | pular CPO + log técnico | Não guardar senha de autos |

Enquanto não houver fixture boa, o ciclo de 10 min é intimação + audiência + upsert da ficha — o painel fica sem histórico, de propósito (ADR-010).

`urlCpo` / `urlPasta` já vêm no GET de processos — não precisa redescobrir.

---

## Validação ao vivo (2026-08-20)

Ciclo real com cookie de `TribunalSession` (`status=ativo`, dentro das 22h), via `backend/scripts/disparar_coleta.py`. Sem payload no Git.

| Checagem | Resultado |
|---|---|
| Cookie autenticou `GET /api/intimacoes`, `/api/audiencias`, `/api/processos?cdsProcesso=` | HTTP 200 nos três; sessão continuou `ativo` |
| Primeiro ciclo | 4 intimações + 1 audiência + 5 fichas (união dos `cdProcesso`) + 5 notificações; todos com `processo_id` preenchido |
| Segundo ciclo (diff) | 3 pipes `sucesso` de novo; delta 0 em intimações, audiências, processos e notificações |
| Cruzamento no painel do advogado | Quantidade, títulos e sala da audiência bateram |
| Tela HTML `/tarefas-adv/intimacoes` | Vazia. As 4 intimações estão em **Manifestações / ciência** |
| Tela `/tarefas-adv/audiencias` | 1 item. Home `tarefas-adv` também mostra o card da audiência |
| Assinar e enviar | Rascunhos de peticionamento — **não** coletados (ADR-010, correto) |

**Timezone da audiência:** o portal mostrou 25/08 às **14:00** (Brasília). O valor persistido foi `…T17:00:00+00:00`. 17:00 UTC = 14:00 BRT — o instante está certo **se** o painel converter para `America/Sao_Paulo`. O padrão antigo deste doc (“naive = já é Brasília”) teria virado 17:00 BRT e **não** batería com o portal. Pendência: no painel sempre formatar em `America/Sao_Paulo`; só revisitar `parse_datetime_esaj` se a UI mostrar 17h.

Smoke (a partir de `backend/`):

```bash
python -m uv run python scripts/verificar_coleta.py --email <email-da-plataforma>
python -m uv run python scripts/disparar_coleta.py --email <email-da-plataforma>
```

Os scripts não imprimem cookie, CPF nem `id_esaj` de intimação. A saída ainda pode ter número CNJ e título — não colar em issue/commit. O logger padrão do `httpx` (que logava a URL completa, com `cdsProcesso` na query, em INFO) foi rebaixado para `WARNING` em `app/services/esaj_http.py` na Etapa 8 — vale para scheduler, scripts e testes.

---

## Padrões seguidos neste contrato

- **Bruto → Pydantic item a item → banco:** `validar_itens` em cada pipe; item malformado é omitido. Um registro ruim não derruba a carteira
- **VARCHAR(255):** `titulo` / `local` / `id_esaj` (e o título dentro da chave composta de audiência) são cortados no ETL (`TITULO_MAX` / `ID_ESAJ_MAX`) — sem migration agora
- **`is_new`:** depois de `gerar_notificacoes`, as linhas recém-persistidas ficam `is_new=False` — a notificação já foi emitida; a flag não mente para o painel
- **Cookie só em memória no job:** decriptar `cookie_encrypted` na hora do GET, nunca logar, nunca devolver na nossa API. `executar_ciclo_usuario` recusa sessão `ativo` com `cookie_expirado()`
- **Diff por unique:** intimação = `id` da API em `id_esaj`; audiência = id composto `cdProcesso|dataAudiencia|titulo` (ADR-010); movimentação = `(processo_id, data, descricao_hash)`; processo = upsert
- **Timezone:** timestamps da API vêm **sem offset**. Validação 2026-08-20: o instante gravado como UTC bateu com a hora de Brasília do portal (17:00 UTC = 14:00 BRT). O painel deve **exibir** em `America/Sao_Paulo`. Não assumir mais, sem conferir, que o naive da API já é horário de Brasília (isso deslocaria +3h na UI).
- **Exemplos neste doc:** sempre sanitizados. `scripts/esaj/results/` permanece gitignorado
- **Escopo:** só XHR das telas do MVP + CPO da capa. Outras rotas (prazos, mensagens, PDF) = backlog quando o UI pedir o campo

---

## Modelo de dados relacionado

Schema atual (sem nova auto-relação):

```mermaid
erDiagram
  users ||--o{ processos : tem
  users ||--o{ intimacoes : tem
  users ||--o{ audiencias : tem
  processos ||--o{ movimentacoes : historico
  processos ||--o{ intimacoes : opcional
  processos ||--o{ audiencias : opcional
  processos ||--o{ notifications : opcional
```

Trecho que o GET de processos alimenta:

```python
class Processo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processos"
    __table_args__ = (UniqueConstraint("user_id", "cd_processo"),)

    user_id: Mapped[uuid.UUID]
    tribunal: Mapped[str]          # "esaj_tjsp" — nosso, não vem da API
    cd_processo: Mapped[str]       # cdProcesso
    nu_processo: Mapped[str | None]
    de_classe: Mapped[str | None]
    de_assunto: Mapped[str | None]
    instancia: Mapped[str | None]
    parte_ativa: Mapped[dict | None]   # JSONB {nome, representada}
    parte_passiva: Mapped[dict | None]
    url_cpo: Mapped[str | None]
    url_pasta: Mapped[str | None]
    status: Mapped[str | None]         # não vem do GET /api/processos
```

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| Login e-SAJ | Cookie válido e warm-up `tarefas-adv` senão as APIs redirecionam para login |
| Credenciais / sessão | `TribunalSession.status == ativo`, cookie presente e **não** expirado (`cookie_expirado()`) |
| Migrations | Tabelas destino já existem |

Módulos que já dependem deste:

| Módulo | Uso |
|---|---|
| Painel de processos | Só campos persistidos aqui; o resto fica ignorado (próxima etapa de produto) |
| Scheduler | Chama `coleta_esaj.executar_ciclo_usuario` por advogado a cada 10 min — ver `/docs/modulos/scheduler.md` |

---

## O que NÃO fazer aqui

- ❌ Não tratar a rota HTML `/tarefas-adv/intimacoes` como a lista que o advogado vê — a API JSON alimenta **Manifestações / ciência**
- ❌ Não commitar `scripts/esaj/results/` nem fixtures com nome, OAB, CPF ou número real
- ❌ Não logar `intimacoes.id` (leva OAB), cookie, nem a URL completa do GET de processos (`cdsProcesso` na query)
- ❌ Não logar o input de `ValidationError` — `validar_itens` só loga tipo do erro e nome do campo
- ❌ Não alargar `id_esaj`/`titulo`/`local` via migration só porque um título longo apareceu — truncar no ETL; migration só se o composto de audiência começar a colidir (backlog)
- ❌ Não deixar `is_new=True` depois de `gerar_notificacoes` — a notificação já foi emitida; a flag mentiria para o painel
- ❌ Não tratar GET `/api/processos` sem `cdsProcesso` como lista da carteira
- ❌ Não assumir que 200 devolveu todos os códigos pedidos
- ❌ Não inventar `id_esaj` de audiência por UUID aleatório a cada ciclo — usar o composto `cdProcesso|dataAudiencia|titulo` (se passar de 255, trunca só o título na chave)
- ❌ Não esperar a carteira completa para começar intimação/audiência/ficha
- ❌ Não gravar petição `AGUARDANDO_ASSINATURA` em `movimentacoes` nem no ciclo de 10 min
- ❌ Não inventar movimentação a partir de `peticoes_diversas` do CPO
- ❌ Não ligar o pipe de movimentações sem fixture CPO com `movimentacoes` preenchido
- ❌ Não modelar apenso/recurso (auto-relação) sem campo no payload
- ❌ Não persistir juiz/foro/delegacia no MVP só porque o CPO tem
- ❌ Não guardar senha de autos / segredo de justiça
- ❌ Não confiar no parser CPO atual para movimentações (array vazio + cabeçalho virando linha)
- ❌ Não varrer o e-SAJ atrás de “todas as APIs” — só XHR das telas que o produto mostra

---

## Decisões aceitas (ADR-010)

| Tema | Escolha |
|---|---|
| Unique de audiência | `id_esaj` composto `cdProcesso={cd}\|dataAudiencia={iso}\|titulo={titulo}`; unique `(user_id, id_esaj)` intacto |
| `situacao` / `dataMovimentacao` da audiência | Não persistem no MVP |
| `cdProcesso` no ciclo | União intimação + audiência + `processos` já salvos; omitido no 200 = skip |
| Carteira completa | Importação à parte; não bloqueia os pipes de monitoramento |
| Movimentações | CPO só com fixture boa + parser que descarta cabeçalho; segredo = pular |
| Petições `tarefas-adv` | Fora do ciclo; não é andamento |
| Item malformado no JSON | Omitido (`validar_itens`); não derruba o pipe |
| Estouro de `VARCHAR(255)` | Truncar `titulo`/`local`/`id_esaj` no ETL; na chave de audiência trunca só o título |
| `is_new` após notificar | `False` — a `Notification` já foi criada |

O PRD falava “salva nova versão”: no schema atual isso **já** é upsert + append, não SCD.

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-08-18 | Catálogo inicial a partir das capturas do lab (JSON tarefas-adv + parse CPO), mapeamento sanitizado, lacunas e decisões em aberto para os pipes |
| 2026-08-18 | Quatro lacunas fechadas (ADR-010): id composto de audiência, carteira em duas camadas, CPO com gate de fixture, petições fora do ciclo |
| 2026-08-20 | Etapa 7: pipes de intimações/audiências/processos, ETL, diff e notificações implementados; scheduler ainda não integrado |
| 2026-08-20 | Validação ao vivo: cookie autenticou as 3 APIs; diff no 2º ciclo = 0; UI de intimações = **Manifestações / ciência**; Assinar e enviar = petições fora do ciclo; instante da audiência em UTC bate com 14h BRT no portal |
| 2026-08-21 | Etapa 8: scheduler passou a chamar o ciclo a cada 10 min (ver `/docs/modulos/scheduler.md`); HTTP 429 ganhou `EsajRateLimitError` dedicado (`bloqueado` + backoff, cookie preservado); logger do `httpx` rebaixado para `WARNING` |
| 2026-08-21 | Hardening: validação item a item (`validar_itens`, sem logar OAB); truncate de `titulo`/`local`/`id_esaj` no ETL; `is_new=False` depois de notificar |
