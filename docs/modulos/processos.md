# Módulo: Painel de Processos e Notificações

> Última atualização: 2026-08-26
> Camada: Backend / Frontend

---

## O que este módulo faz

Expõe ao advogado autenticado os processos, intimações, audiências, movimentações e notificações já persistidos pelo ciclo e-SAJ. A home pós-login (`/`) deixa de usar mocks da ficha: lista e detalhe vêm da API. Campos que o e-SAJ ainda não entrega (prazo, objeto da ação, PDFs) aparecem como **"Não disponível"** — nunca como texto jurídico inventado em um processo real. Andamentos do CPO (movimentações) deixaram de ser um desses placeholders em 2026-08-22 (ADR-012). Capa, partes, petições diversas e audiências da página do CPO passaram a complementar o detalhe em 2026-08-25 (ADR-013), sem mudar o card da home (polo JSON). Sem dado + CPO ainda `pendente`: **"Ainda não buscado no CPO"**; sem dado após o sync: **"Não disponível"**.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/api/processos.py` | `GET /processos`, `GET /processos/{id}` |
| `backend/app/api/notifications.py` | `GET /notifications`, `PATCH /{id}`, `POST /marcar-lidas` |
| `backend/app/services/painel.py` | Consultas com `WHERE user_id = …` e mapeamento para schemas públicos |
| `backend/app/schemas/processo.py` | `ProcessoListSchema`, `ProcessoDetalheSchema` (capa CPO, partes, petições, audiências CPO só no detalhe) |
| `backend/app/schemas/notification.py` | `NotificationPublicSchema` |
| `frontend/src/features/processos/processos.api.ts` | Chamadas tipadas da lista/detalhe |
| `frontend/src/features/processos/processos.types.ts` / `processos.constants.ts` | Contratos públicos e query keys (`['processos']`, `['processos', id]`) |
| `frontend/src/features/processos/DashboardPage.tsx` | Home: busca, filtro de portal, seleção |
| `frontend/src/features/processos/ProcessoSidebar.tsx` / `ArbitroPesquisa.tsx` | Lista + busca/filtro de portal |
| `frontend/src/features/processos/ProcessoCard.tsx` / `ProcessoDetalhe.tsx` | Card (polo JSON) e ficha (capa/partes CPO) |
| `frontend/src/features/processos/GabineteDocumentos.tsx` | Links da pasta/CPO no e-SAJ — PDF nunca é baixado |
| `frontend/src/features/processos/IntimacaoTimeline.tsx` | Manifestações / ciência |
| `frontend/src/features/processos/AudienciaLista.tsx` | Audiências da agenda JSON |
| `frontend/src/features/processos/AudienciaCpoLista.tsx` | Audiências da capa CPO (bloco separado) |
| `frontend/src/features/processos/PeticoesDiversasLista.tsx` | Petições diversas do CPO |
| `frontend/src/features/processos/MovimentacoesTimeline.tsx` | Histórico de movimentações do CPO (mais recente primeiro); ícone + link do documento no e-SAJ |
| `frontend/src/features/processos/processos.urls.ts` | Só aceita `https://esaj.tjsp.jus.br` em `href` da SPA |
| `frontend/src/features/processos/Navbar.tsx` | Barra clara: seções + sino + Configurações + Sair |
| `frontend/src/features/processos/nav.constants.ts` | Labels e rotas das seções da navbar |
| `frontend/src/features/secoes/SecaoPlaceholderPage.tsx` | Página em branco das seções ainda sem módulo |
| `frontend/src/features/notificacoes/notifications.api.ts` / `notifications.constants.ts` | Lista, marcar lida e query key `['notifications']` |

A página `/elaboracao/$processoId` **continua mock** (IDs numéricos). O botão Elaborar no detalhe real está desabilitado de propósito.

Rotas autenticadas da navbar (além de `/` e `/configuracoes`): `/peticionamento`, `/consulta-pasta`, `/intimacoes-diretas`, `/certidoes`, `/custas-dare`, `/pautas`, `/push-robos`, `/validar-assinatura`. Cada uma é um placeholder com título e uma frase — ainda não chamam API nem inventam fluxo jurídico. O badge amarelo em Intimações Diretas só aparece com notificações `tipo=intimacao` não lidas.

---

## Endpoints

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/processos` | Lista do advogado. Query `q` (número, classe, assunto, nome da parte ativa) | Bearer |
| GET | `/processos/{id}` | Ficha + intimações + audiências JSON + movimentações + capa CPO + `partes_cpo` + `peticoes_diversas` + `audiencias_cpo` + flags `sem_incidentes`/`sem_apensos` + `movimentacoes_status`. 404 se não for dono | Bearer |
| GET | `/notifications` | Lista (não lidas primeiro). Query `somente_nao_lidas` | Bearer |
| PATCH | `/notifications/{id}` | `{ "is_read": true }` | Bearer |
| POST | `/notifications/marcar-lidas` | Marca todas do usuário | Bearer |

> Rotas protegidas usam `Depends(get_current_user)`.
> `user_id` nunca é aceito via body ou query — sempre vem do JWT.
> Processo/notificação de outro usuário: **404**, não 403 (não vaza existência).
> `id_esaj` **nunca** sai no JSON (intimação carrega OAB).

---

## Funções e hooks públicos (frontend)

| Nome | Arquivo | Descrição |
|---|---|---|
| `listarProcessos` / `buscarProcesso` | `features/processos/processos.api.ts` | HTTP tipado |
| `listarNotificacoes` / `marcarNotificacaoLida` / `marcarTodasNotificacoesLidas` | `features/notificacoes/notifications.api.ts` | HTTP tipado |
| `formatarDataSP` / `formatarDataHoraSP` / `textoCampoCpo` | `features/processos/processos.dates.ts` | Exibição em `America/Sao_Paulo`; placeholder CPO pendente vs. após sync |
| `hrefDocumentoMovimentacao` | `features/processos/processos.urls.ts` | Href do documento: URL direta ou ficha CPO; rejeita host/`javascript:` |
| `DashboardPage` | `features/processos/DashboardPage.tsx` | Orquestra lista + detalhe |
| `Navbar` (`onAbrirProcesso`) | `features/processos/Navbar.tsx` | Seções, sino, Configurações, Sair; clique na notificação foca o processo (`?processo=` fora da home) |
| `limparQueriesDaSessao` | `lib/session-queries.ts` | Remove queries de credenciais, processos e notificações |
| `SECOES_NAV` | `features/processos/nav.constants.ts` | Itens do menu central |
| `SecaoPlaceholderPage` | `features/secoes/SecaoPlaceholderPage.tsx` | Título + descrição das seções ainda sem módulo |

TanStack Query: chave `PROCESSOS_QUERY_KEY` (`['processos']` / `['processos', id]`) e `NOTIFICATIONS_QUERY_KEY` (`['notifications']`). Logout e refresh expirado usam `limparQueriesDaSessao` (credenciais + processos + notificações). Clique no sino fora da home navega para `/?processo=<uuid>`.

---

## Padrões seguidos neste módulo

- **Autenticação:** `Depends(get_current_user)` em toda rota
- **Ownership:** `WHERE user_id = current_user.id` no banco — nunca filtrar em Python depois de buscar tudo
- **Resposta:** Pydantic `*PublicSchema` — nunca ORM
- **Sem OAB na API:** mapper omite `id_esaj`; testes travam isso
- **Texto, não HTML:** `descricao`/`message` renderizados como texto (`whitespace-pre-wrap`); sem `dangerouslySetInnerHTML`
- **Placeholder honesto:** campo sem coleta = “Não disponível” / empty state — não mistura mock com CNJ real
- **Datas:** persistidas em timestamptz; o painel formata em `America/Sao_Paulo`
- **404 cruzado:** UUID válido de outro advogado não confirma que o recurso existe
- **Movimentações sem hora:** `data_movimentacao` do CPO vem `dd/mm/aaaa` sem hora (meia-noite SP); o frontend usa `formatarDataSP` (não `formatarDataHoraSP`) para não sugerir uma hora que o e-SAJ nunca informou
- **Movimentações são só o que já foi buscado:** a lista não é o histórico completo do e-SAJ até o throttle (`Processo.movimentacoes_synced_at`, ADR-012) passar por aquele processo — pode aparecer incompleta num processo com muitos andamentos
- **Título não se repete na descrição pública:** `movimentacao_para_publico` omite a primeira linha de `descricao` quando ela é igual ao `titulo` (o texto completo permanece no banco para o hash)
- **CPO sem acesso pleno:** `movimentacoes_status=indisponivel` — nunca pedimos senha dos autos; `pendente` = o lote do ciclo ainda não passou por aquele processo
- **Documento da movimentação:** ícone + link “Abrir documento no e-SAJ”. `url_documento` só quando o CPO deu `abrirDocumentoVinculadoMovimentacao.do` em https no host do e-SAJ; se o portal apontou `#liberarAutoPorSenha`, `tem_documento=true` e o link abre a ficha CPO (`url_cpo`). PDF nunca é baixado nem proxied.
- **`url_cpo` no banco e no fetch:** só `https://esaj.tjsp.jus.br/cpopg/...` (`url_cpo_publica`); o pipe não GET em URL de outro host
- **Throttle CPO:** `movimentacoes_synced_at` só após savepoint ok (ou senha dos autos); `IntegrityError` não marca sincronizado
- **Incidentes/apensos:** só empty state quando a flag é `true`; `null` + status `pendente` não inventa texto; `True` no banco não volta a `False` só porque o marcador sumiu do HTML
- **Capa CPO só no detalhe:** foro, vara, juiz, área, valor da ação, distribuição, controle e `partes_cpo` não entram na lista/card (ADR-013)
- **Duas listas de audiência:** `AudienciaLista` = JSON da carteira; `AudienciaCpoLista` = tabela da capa. Não misturar.

---

## Modelo de dados relacionado

```python
class Processo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processos"
    user_id: Mapped[uuid.UUID]          # unique com cd_processo
    tribunal: Mapped[str]               # "esaj_tjsp"
    nu_processo: Mapped[str | None]     # CNJ
    de_classe / de_assunto / instancia          # JSON da carteira
    parte_ativa / parte_passiva                 # JSONB {nome, representada} — card
    url_cpo / url_pasta
    last_synced_at
    movimentacoes_synced_at                     # throttle de todo o CPO
    foro / vara / juiz / distribuicao / controle / area / valor_acao
    partes_cpo                                  # JSONB [{papel, nome, advogados}]
    sem_incidentes / sem_apensos                # None = CPO ainda não passou

class Intimacao(...):
    # id_esaj no banco, NUNCA na API pública
    titulo, descricao, ciencia, data_movimentacao, processo_id

class Audiencia(...):
    titulo, data_audiencia, local, processo_id  # agenda JSON

class AudienciaCpo(...):
    data_audiencia, titulo, situacao, qt_pessoas  # capa CPO; unique identidade_hash

class PeticaoDiversa(...):
    data_peticao, tipo, protocolo  # unique identidade_hash; protocolo ou data|tipo|texto_extra

class Movimentacao(...):
    # unique (processo_id, data_movimentacao, descricao_hash) — ADR-012
    titulo, descricao, data_movimentacao, processo_id
    tem_documento, url_documento  # URL só https do e-SAJ; senha dos autos nunca vira href

class Notification(...):
    tipo  # intimacao | audiencia | movimentacao (sistema ainda não gerado)
    titulo, message, is_read, processo_id
```

A lista da home **não** é a carteira completa do e-SAJ — só processos que passaram pelo ciclo (intimação/audiência ou já persistidos).

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| Autenticação | `CurrentUser` / Bearer + refresh |
| Contrato e-SAJ / ETL | Origem dos campos persistidos (`/docs/modulos/esaj-apis.md`) |
| Scheduler | Gera as linhas que o painel lê; não é chamado pela UI |
| Credenciais | Sem sessão `ativo` o ciclo não alimenta o banco |

---

## O que NÃO fazer aqui

- ❌ Não devolver `id_esaj` de intimação/audiência — leva OAB
- ❌ Não aceitar `user_id` no query/body/path além do UUID do **recurso**
- ❌ Não responder 403 em recurso de outro usuário — use 404
- ❌ Não inventar prazo, objeto da ação ou PDF em processo real — magistrado/foro/vara vêm do CPO quando o lote já passou (ADR-013)
- ❌ Não religar o botão Elaborar enquanto `/elaboracao/$processoId` exigir id numérico mock
- ❌ Não usar `dangerouslySetInnerHTML` com texto vindo do e-SAJ
- ❌ Não tratar a lista do painel como importação da carteira completa
- ❌ Não baixar, guardar ou fazer proxy de PDF da pasta digital — o advogado abre o e-SAJ no próprio browser
- ❌ Não colocar `<a>` dentro de `<button>` no card da movimentação
- ❌ Não transformar `#liberarAutoPorSenha` em `href` da SPA
- ❌ Não misturar `audiencias_cpo` com a agenda JSON no mesmo bloco
- ❌ Não colocar capa CPO no card da home — o polo continua sendo o JSON
- ❌ Não recolocar na navbar badges de portal, “Auditoria digital” ou status ICP-Brasil — ficaram de fora de propósito
- ❌ Não fingir peticionamento, pasta digital, certidão, DARE, pauta, push ou validação de assinatura nas rotas placeholder — só título + descrição até o módulo existir

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-08-21 | Primeira exposição HTTP + home ligada ao banco: lista/detalhe, intimações no lugar da timeline mock, audiências, sino de notificações, placeholders nos campos sem coleta |
| 2026-08-22 | `ProcessoDetalheSchema.movimentacoes` (mais recente primeiro) + `MovimentacaoPublicSchema`; `MovimentacoesTimeline.tsx` no detalhe real; notificação `tipo="movimentacao"` (ADR-012) |
| 2026-08-24 | API pública deixa de repetir o título na descrição; `movimentacoes_status` distingue CPO pendente, bloqueado (sem senha de autos) e ok |
| 2026-08-24 | Ícone “há documento” + link para o e-SAJ (`tem_documento` / `url_documento`); `#liberarAutoPorSenha` não vira URL — cai na ficha CPO |
| 2026-08-25 | Detalhe ganha capa CPO, partes, petições diversas, audiências da página e empty states de incidentes/apensos (ADR-013); lista/card inalterados |
| 2026-08-26 | Navbar clara com menu de seções (mock Studio) + sino/Configurações/Sair; seções novas são placeholders autenticados |
| 2026-08-26 | Hardening: throttle CPO no savepoint, whitelist `url_cpo`, cache da sessão no refresh, flags CPO, `?processo=` no sino |
