# Módulo: Painel de Processos e Notificações

> Última atualização: 2026-09-07
> Camada: Backend / Frontend

---

## O que este módulo faz

Expõe ao advogado autenticado os processos, intimações, audiências, movimentações e notificações já persistidos pelo ciclo e-SAJ. A home pós-login (`/`) deixa de usar mocks da ficha: lista e detalhe vêm da API. Campos que o e-SAJ ainda não entrega (prazo, objeto da ação, PDFs) aparecem como **"Não disponível"** — nunca como texto jurídico inventado em um processo real. Andamentos do CPO (movimentações) deixaram de ser um desses placeholders em 2026-08-22 (ADR-012). Capa, partes, petições diversas e audiências da página do CPO passaram a complementar o detalhe em 2026-08-25 (ADR-013), sem mudar o card da home (polo JSON). Sem dado + CPO ainda `pendente`: **"Ainda não buscado no CPO"**; sem dado após o sync: **"Não disponível"**.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/api/processos.py` | `GET /processos`, `GET /processos/{id}`, `PATCH`, `GET /intimacoes`, `GET /audiencias` |
| `backend/app/api/notifications.py` | `GET /notifications`, `PATCH /{id}`, `POST /marcar-lidas` |
| `backend/app/services/painel.py` | Consultas com `WHERE user_id = …` e mapeamento para schemas públicos |
| `backend/app/schemas/processo.py` | `ProcessoListSchema`, `ProcessoDetalheSchema` (capa CPO, partes, petições, audiências CPO só no detalhe) |
| `backend/app/schemas/notification.py` | `NotificationPublicSchema` |
| `frontend/src/features/processos/processos.api.ts` | Chamadas tipadas da lista/detalhe |
| `frontend/src/features/processos/processos.types.ts` / `processos.constants.ts` | Contratos públicos e query keys (`['processos']`, `['processos', id]`) |
| `frontend/src/features/processos/DashboardPage.tsx` | Home: busca, filtro de portal, seleção |
| `frontend/src/features/processos/ProcessoSidebar.tsx` / `ArbitroPesquisa.tsx` | Lista + busca/filtro de portal |
| `frontend/src/features/processos/ProcessoCard.tsx` | Card da lista (polo JSON); só visual alinhado ao mock Studio |
| `frontend/src/features/processos/ProcessoDetalhe.tsx` | Orquestra cabeçalho + andamentos |
| `frontend/src/features/processos/ProcessoCabecalho.tsx` | Tags, CNJ, pin, capa e ações (pasta digital / Elaborar) |
| `frontend/src/features/processos/ProcessoAndamentos.tsx` | Lista de movimentações + detalhe |
| `frontend/src/features/processos/DetalheMovimentacao.tsx` / `VisualizadorPdfModal.tsx` | Texto da movimentação; modal visual de PDF (abre o e-SAJ) |
| `frontend/src/features/processos/GabineteDocumentos.tsx` | Links da pasta/CPO no e-SAJ — PDF nunca é baixado |
| `frontend/src/features/processos/processos.format.ts` | CNJ, grau, foro/área/vara, escape para impressão |
| `frontend/src/features/processos/IntimacaoTimeline.tsx` | Manifestações / ciência |
| `frontend/src/features/processos/AudienciaLista.tsx` | Audiências da agenda JSON |
| `frontend/src/features/processos/AudienciaCpoLista.tsx` | Audiências da capa CPO (bloco separado) |
| `frontend/src/features/processos/PeticoesDiversasLista.tsx` | Petições diversas do CPO |
| `frontend/src/features/processos/MovimentacoesTimeline.tsx` | Histórico de movimentações do CPO (mais recente primeiro); clique inspeciona à direita |
| `frontend/src/features/processos/processos.urls.ts` | Só aceita `https://esaj.tjsp.jus.br` em `href` da SPA |
| `frontend/src/features/processos/AppChrome.tsx` | Shell autenticado: navbar + rail só em Gerências |
| `frontend/src/features/processos/AppSidebar.tsx` | Rail de Gerências (abaixo da navbar): Andamentos, Consultas, Intimações, Audiências, Push Robôs |
| `frontend/src/features/processos/Navbar.tsx` | Barra de largura total: áreas (Gerências/Elaborações/Drive/Tarefas) + sino + Configurações + Sair |
| `frontend/src/features/processos/nav.constants.ts` | Seções laterais e do topo; `estaEmGerencias` / `secaoTopoAtiva` |
| `frontend/src/features/consulta/ConsultaPastaPage.tsx` | Consulta / Pasta Digital — processos reais; peças = docs/petições coletados |
| `frontend/src/features/intimacoes/IntimacoesDiretasPage.tsx` | Intimações Diretas — lista real; ciência/peticionar desabilitados |
| `frontend/src/features/pautas/PautasPage.tsx` | Pautas — audiências reais; mock só se a lista vier vazia (aviso visível) |
| `frontend/src/features/push/PushRobosPage.tsx` | Push Robôs — processos do ciclo; form/PJe ilustrativos com aviso |
| `frontend/src/features/secoes/SecaoPlaceholderPage.tsx` | Página em branco (Drive, Tarefas, Elaborações, Peticionamento, Custas DARE) |
| `frontend/src/features/secoes/SecaoShell.tsx` | AppChrome + padding das seções de Gerências (Consulta, Intimações, Pautas, Push) |
| `frontend/src/features/elaboracao/ElaboracaoPage.tsx` | Minuta 3 colunas; cabeçalho/ficha reais; editor TipTap |
| `frontend/src/features/elaboracao/useMinutaEditor.ts` | Instância TipTap (formatação local; sem code/heading) |
| `frontend/src/features/elaboracao/GrifoSelecaoPanel.tsx` | Painel visual de trecho selecionado (sem IA) |
| `frontend/src/features/elaboracao/elaboracao.processo.ts` | CNJ/polos/foro/valor e completude a partir da ficha real |
| `frontend/src/features/elaboracao/elaboracao.minuta.ts` | HTML da minuta (dados reais escapados) + opções da toolbar |
| `frontend/src/features/notificacoes/notifications.api.ts` / `notifications.constants.ts` / `notifications.query.ts` | Lista, marcar lida, query key `['notifications']` e polling do sino (60s, só aba visível) |

A página `/elaboracao/$processoId` usa o UUID real. O botão Elaborar no detalhe abre essa rota. O editor (TipTap) formata o texto. O corpo jurídico **não** é gerado por IA — só o cabeçalho usa dados do e-SAJ, escapados antes de virar HTML. O painel de grifo é visual. Copiar usa a área de transferência. Peça-modelo (TXT/PDF/DOCX) e versões da minuta ficam **só neste browser** (`localStorage` para versões) — nada vai ao servidor. Word/PDF/Extrair/Elaborar e jurisprudência oficial continuam desabilitados.

Navegação autenticada em dois eixos (ADR-014). A navbar cobre a largura toda: Gerências (abre `/`), Elaborações, Drive e Tarefas. A rail esquerda só existe dentro de Gerências (`/`, `/consulta-pasta`, `/intimacoes-diretas`, `/pautas`, `/push-robos`) e começa abaixo da navbar. `/gerencias` redireciona para Andamentos. Elaborações, Drive e Tarefas são placeholders (sem rail). Peticionamento, Custas DARE, Certidões e Validar Assinatura saíram do menu; `/peticionamento` e `/custas-dare` ainda existem como placeholder. O ponto âmbar em Intimações só aparece com notificações `tipo=intimacao` não lidas. `/elaboracao/$processoId` continua sendo a minuta de um processo — não confundir com `/elaboracoes`.

---

## Endpoints

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/processos` | Lista do advogado. Query `q` (número, classe, assunto, nome da parte ativa). Fixados primeiro | Bearer |
| GET | `/processos/{id}` | Ficha + intimações + audiências JSON + movimentações + capa CPO + `partes_cpo` + `peticoes_diversas` + `audiencias_cpo` + flags `sem_incidentes`/`sem_apensos` + `movimentacoes_status` + `fixado` + `datajud` (complemento público do CNJ, ver `/docs/modulos/datajud.md`). 404 se não for dono | Bearer |
| PATCH | `/processos/{id}` | `{ "fixado": true \| false }` — só a preferência do advogado. 404 se não for dono. Resposta `{ id, fixado }` | Bearer |
| GET | `/intimacoes` | Intimações do advogado + CNJ/vara do processo (sem `id_esaj`) | Bearer |
| GET | `/audiencias` | Audiências da agenda JSON + capa CPO, com polo/foro do processo (sem `id_esaj`) | Bearer |
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
| `listarProcessos` / `buscarProcesso` / `atualizarFixado` / `listarIntimacoes` / `listarAudiencias` | `features/processos/processos.api.ts` | HTTP tipado |
| `formatarNumeroCnj` / `tagTribunalGrau` / `juntarLocalProcesso` | `features/processos/processos.format.ts` | Exibição do CNJ e das tags da ficha |
| `listarNotificacoes` / `marcarNotificacaoLida` / `marcarTodasNotificacoesLidas` | `features/notificacoes/notifications.api.ts` | HTTP tipado |
| `formatarDataSP` / `formatarDataHoraSP` / `textoCampoCpo` | `features/processos/processos.dates.ts` | Exibição em `America/Sao_Paulo`; placeholder CPO pendente vs. após sync |
| `hrefDocumentoMovimentacao` | `features/processos/processos.urls.ts` | Href do documento: URL direta ou ficha CPO; rejeita host/`javascript:` |
| `DashboardPage` | `features/processos/DashboardPage.tsx` | Orquestra lista + detalhe |
| `AppChrome` | `features/processos/AppChrome.tsx` | Navbar em toda rota autenticada; rail só se `estaEmGerencias` |
| `Navbar` (`onAbrirProcesso`) | `features/processos/Navbar.tsx` | Áreas do topo, sino, Configurações, Sair; clique na notificação foca o processo (`?processo=` fora da home) |
| `limparQueriesDaSessao` | `lib/session-queries.ts` | Remove queries de credenciais, processos e notificações |
| `SECOES_LATERAL` / `SECOES_TOPO` / `estaEmGerencias` / `secaoTopoAtiva` | `features/processos/nav.constants.ts` | Rail só em Gerências; Elaborações cobre também `/elaboracao/$processoId` |
| `extrairDadosElaboracao` / `completudeDadosProcesso` / `montarEnderecamento` | `features/elaboracao/elaboracao.processo.ts` | Campos reais da minuta; sem inventar texto jurídico |
| `montarHtmlMinuta` / `escaparHtml` | `features/elaboracao/elaboracao.minuta.ts` | HTML inicial da minuta; texto do e-SAJ sempre escapado |
| `validarArquivoModelo` / `posicaoPainelGrifo` / `alinhamentoDoNo` | `features/elaboracao/elaboracao.ui.ts` | Upload local da peça-modelo; painel de grifo; justificar da toolbar |
| `adicionarVersao` / `lerVersoes` | `features/elaboracao/elaboracao.versoes.ts` | Histórico local da minuta (sem API) |
| `SecaoPlaceholderPage` | `features/secoes/SecaoPlaceholderPage.tsx` | Título + descrição das seções ainda sem módulo |

TanStack Query: chave `PROCESSOS_QUERY_KEY` (`['processos']` / `['processos', id]`) e `NOTIFICATIONS_QUERY_KEY` (`['notifications']`). O sino e a rail compartilham `notificacoesListQueryOptions`: polling a cada 60s só com a aba visível (`refetchIntervalInBackground: false`) — o ciclo e-SAJ continua de 10 min; isso só atualiza o badge sem reload. Logout e refresh expirado usam `limparQueriesDaSessao` (credenciais + processos + notificações). Clique no sino fora da home navega para `/?processo=<uuid>`.

---

## Padrões seguidos neste módulo

- **Autenticação:** `Depends(get_current_user)` em toda rota
- **Ownership:** `WHERE user_id = current_user.id` no banco — nunca filtrar em Python depois de buscar tudo. Join de intimação/audiência com `Processo` também exige `Processo.user_id` no `ON` (`_on_processo_do_usuario`)
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
- **Documento da movimentação:** ícone na lista + “Visualizar PDF” no detalhe. O modal mostra o **texto coletado**; “Baixar PDF” abre o e-SAJ no browser do advogado. `url_documento` só quando o CPO deu `abrirDocumentoVinculadoMovimentacao.do` em https no host do e-SAJ; se o portal apontou `#liberarAutoPorSenha`, `tem_documento=true` e o link abre a ficha CPO (`url_cpo`). PDF nunca é baixado nem proxied.
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
    fixado                                      # preferência do advogado na home
    foro / vara / juiz / distribuicao / controle / area / valor_acao
    partes_cpo                                  # JSONB [{papel, nome, advogados}]
    sem_incidentes / sem_apensos                # None = CPO ainda não passou

class ProcessoDatajud(...):
    # Tabela separada (1:1) — complemento público do CNJ, nunca sobrescreve
    # os campos acima. Ver `/docs/modulos/datajud.md` (Etapa 9 / ADR-015).

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
- ❌ Não inventar texto jurídico da minuta com CNJ real — só cabeçalho/ficha vêm do e-SAJ
- ❌ Não passar nome/CNJ do e-SAJ para o TipTap sem `escaparHtml`
- ❌ Não tratar o painel de grifo / Elaborar como IA operacional
- ❌ Não tratar jurisprudência ilustrativa da elaboração como dado oficial
- ❌ Não enviar arquivo da peça-modelo ao backend — fica no browser
- ❌ Não tratar `localStorage` de versões como backup do servidor
- ❌ Não usar `dangerouslySetInnerHTML` com texto vindo do e-SAJ
- ❌ Não tratar a lista do painel como importação da carteira completa
- ❌ Não baixar, guardar ou fazer proxy de PDF da pasta digital — o advogado abre o e-SAJ no próprio browser
- ❌ Não fingir visualizador com PDF real, folha, ICP-Brasil ou número de páginas do tribunal — o modal é o texto da movimentação
- ❌ Não colocar `<a>` dentro de `<button>` no card da movimentação
- ❌ Não transformar `#liberarAutoPorSenha` em `href` da SPA
- ❌ Não misturar `audiencias_cpo` com a agenda JSON no mesmo bloco
- ❌ Não colocar capa CPO no card da home — o polo continua sendo o JSON
- ❌ Não recolocar na navbar badges de portal, “Auditoria digital” ou status ICP-Brasil — ficaram de fora de propósito
- ❌ Não devolver Andamentos, Consultas, Intimações, Audiências ou Push Robôs para a navbar superior — esses itens ficam na rail esquerda
- ❌ Não fingir peticionamento, certidão, DARE, sala virtual, ciência ICP ou validação de assinatura — botões dessas ações ficam desabilitados
- ❌ Não misturar mock jurídico com CNJ real na mesma lista (Pautas só usa `pautas.mock` se a API vier vazia, com aviso; Push marca PJe/form como ilustrativo)

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
| 2026-08-28 | Home em 4 containers (lateral, árbitro, ficha, movimentações+detalhe); pin (`fixado`); CNJ formatado; modal de PDF sem proxy |
| 2026-08-28 | Navbar sem Peticionamento/Custas DARE; Consulta, Intimações, Pautas e Push com visual do Studio + dados reais quando existem |
| 2026-09-01 | Navbar sem Certidões/Validar Assinatura (rotas apagadas); padding lateral maior nas seções; Consulta sem botões avançada/livre |
| 2026-09-02 | Elaboração: editor TipTap (formatação local) + painel de grifo visual; HTML da minuta escapa dados do e-SAJ |
| 2026-09-02 | Grifo acima no rodapé; justificar desliga; Dialog/Switch opacos; peça-modelo e versões só no browser |
| 2026-09-02 | Rail esquerda (Andamentos/Consultas/Intimações/Audiências/Push Robôs) + navbar (Gerências/Elaborações/Drive/Tarefas); placeholders vazios nas áreas novas |
| 2026-09-02 | Rail só em Gerências e abaixo da navbar; Gerências abre Andamentos; abas do topo em faixa larga com ícone |
| 2026-09-03 | ADR-014: chrome em dois eixos documentado no INDEX |
| 2026-09-03 | Join intimação/audiência ↔ processo exige `user_id` no SQL |
| 2026-09-06 | `ProcessoDetalheSchema.datajud` — complemento público somente-leitura do CNJ, seção separada na ficha (Etapa 9 / ADR-015, ver `/docs/modulos/datajud.md`) |
| 2026-09-07 | Sino faz polling de 60s (aba visível) — badge atualiza sem recarregar a página |
