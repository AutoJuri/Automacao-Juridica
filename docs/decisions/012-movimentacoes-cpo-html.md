# ADR-012: Pipe de movimentações via HTML do CPO (throttle, seletor real, detecção de bloqueio)

**Data:** 2026-08-22
**Status:** Aceito

---

## Contexto

O ADR-010 deixou o pipe de movimentações bloqueado até existir "uma captura CPO com `movimentacoes` preenchido" — as capturas de lab disponíveis então tinham o array vazio. Nesta etapa, `backend/scripts/capturar_cpo.py` foi usado para baixar o HTML real do CPO (`GET /cpopg/show.do`) de 5 processos de uma sessão `ativo`. Uma delas era um processo sem acesso pleno (mostrou só o popup de senha); as outras 4 trouxeram entre 15 e 467 movimentações cada. As capturas ficam em `scripts/esaj/results/` (gitignorado) — nunca entram no Git.

A inspeção dessas capturas mudou três suposições do ADR-010:

1. **Não existe o problema de "header-as-row"** nas movimentações (isso era uma preocupação sobre `peticoes_diversas`, um bloco diferente, que continua fora de escopo). As 662 linhas somadas nas 4 capturas acessíveis tinham `data` e `descricao` sempre preenchidos.
2. **O HTML não pagina via AJAX.** Existem dois `<tbody>`: `tabelaUltimasMovimentacoes` (só as últimas N, visível por padrão) e `tabelaTodasMovimentacoes` (**todas** as movimentações, com `style="display: none"` — some visualmente, mas o HTML já vem completo). O parser deve usar sempre o segundo.
3. **O popup de senha não é sinal confiável de bloqueio.** O formulário `#popupSenha` ("Se for uma parte ou interessado, digite a senha do processo") é um template oculto presente em **toda** página do CPO, inclusive nas 4 acessíveis. O sinal real de "sem acesso pleno" é a **ausência** do `tbody#tabelaTodasMovimentacoes` no HTML.

## Decisão

1. **Fonte de dados:** `tbody#tabelaTodasMovimentacoes`. Cada linha é um `tr.containerMovimentacao` com `td.dataMovimentacao` (texto `dd/mm/aaaa`, sem hora) e `td.descricaoMovimentacao` (texto livre: primeira linha = título curto, ex. "Certidão de Publicação Expedida"; linhas seguintes, quando existem, vêm de um `<span style="font-style: italic;">` com detalhe — ex. "Relação: X", "Teor do ato: ...", "Advogados(s): ..."). `titulo` = primeira linha; `descricao` = texto completo (título + detalhe), igual ao que o portal mostra.
2. **Bloqueio/segredo de justiça:** `tabelaTodasMovimentacoes` ausente no HTML ⇒ `requer_senha_processo=True`, lista vazia. Nunca inferir isso a partir do texto do popup de senha (presente mesmo em página liberada) nem pedir/guardar senha de autos.
3. **Linha malformada** (sem `data` ou sem `descricao`) é omitida, só loga contagem — nunca derruba o parse da página inteira nem inventa valor.
4. **Throttle por processo, não por advogado.** Nova coluna `Processo.movimentacoes_synced_at` (nullable). A cada ciclo de 10 min, busca o HTML de só um lote pequeno (`pipe_movimentacoes.MOVIMENTACOES_LOTE = 5`) por advogado — o menor código, ordenado por `movimentacoes_synced_at ASC NULLS FIRST` (round-robin: quem nunca foi buscado tem prioridade; depois quem está mais atrasado). Fetch de página HTML inteira é bem mais caro que os GETs JSON dos outros pipes, e o ciclo tem orçamento de 60s por advogado.
5. **`movimentacoes_synced_at` só avança para quem teve fetch bem-sucedido e persistência ok** (ou `requer_senha_processo`, que é fetch válido sem gravar capa). Falha pontual (`EsajPortalIndisponivelError`) ou `IntegrityError` no savepoint **não** atualiza o timestamp — o processo volta à fila no próximo ciclo. Sessão inválida ou rate limit sobem para o orquestrador, mesmo tratamento dos outros pipes.
6. **Dedupe:** `(processo_id, data_movimentacao, descricao_hash)` — reaproveita o unique já existente no model `Movimentacao` (`descricao_hash` é SHA-256 de `descricao`, calculado via `@validates` do model; o `descricao` em si não entra no unique porque índice do Postgres não aceita valores muito grandes).
7. **Notificação:** `Notification.tipo = "movimentacao"`, mesma mecânica de `is_new=False` após `gerar_notificacoes` que intimação/audiência já usam.

## Alternativas consideradas

- Parsear `tabelaUltimasMovimentacoes` em vez de `tabelaTodasMovimentacoes`: mais simples, mas perde histórico (só mostra as últimas N que o portal decide exibir).
- Manter a heurística de "descartar primeira linha se for cabeçalho" prevista no ADR-010: não existe essa sujeira nas movimentações reais (era sobre `peticoes_diversas`); adicionar a heurística mesmo assim arriscaria descartar a movimentação mais recente por engano.
- Detectar bloqueio pelo texto "digite a senha do processo": falso positivo garantido — esse HTML está presente em toda página, inclusive as 4 capturas acessíveis.
- Buscar o HTML do CPO de todos os processos do advogado a cada ciclo: mais simples, mas um advogado com muitos processos furaria o orçamento de 60s por ciclo (página HTML inteira é ordens de magnitude mais pesada que os GETs JSON).

## Consequências

- Pipe novo (`pipe_movimentacoes.py`) + parser (`esaj_cpo_parser.py` sobre `esaj_cpo_raw.py`) + migration (`Processo.movimentacoes_synced_at`) + ETL/diff (`movimentacao_para_campos`, `diff_e_persistir_movimentacoes`) + notificação `tipo=movimentacao` + API (`ProcessoDetalheSchema.movimentacoes`) + frontend (`MovimentacoesTimeline.tsx`).
- Processo com muitas movimentações (467 numa das capturas) demora vários ciclos de 10 min para "esvaziar a fila" pela primeira vez (round-robin do lote de 5) — aceitável no MVP; se ficar lento demais na prática, é o próximo ponto a revisitar (aumentar `MOVIMENTACOES_LOTE` ou paralelizar fetches).
- `peticoes_diversas` ficou fora desta etapa (não apareceu nas 5 capturas). Superado pelo ADR-013: o mesmo HTML do lote passou a persistir petições diversas, capa, partes e audiências CPO.
- ADR-010 item 3 ("Movimentações: só depois de uma captura CPO com `movimentacoes` preenchido... parser que ignore cabeçalho de tabela") está superado por este ADR — a fixture existe e o parser real não precisou da heurística de cabeçalho.
