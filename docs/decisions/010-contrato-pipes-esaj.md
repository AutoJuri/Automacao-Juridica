# ADR-010: Contrato dos pipes e-SAJ (chave de audiência, carteira, CPO, petições)

**Data:** 2026-08-18
**Status:** Aceito

---

## Contexto

As capturas do lab (`scripts/esaj/results/`, gitignoradas) mostram que o PRD não bate com o payload real em quatro pontos: audiência sem `id`, GET de processos que não lista a carteira, movimentações só no HTML do CPO (parser ainda sem fixture boa) e `/api/peticoes` como rascunho de assinatura, não andamento. Precisava fechar isso antes da Etapa 7.

## Decisão

1. **`id_esaj` de audiência é composto nosso**, estável, no mesmo espírito da intimação: `cdProcesso={cd}|dataAudiencia={iso}|titulo={titulo}`. Unique `(user_id, id_esaj)` permanece. Sem UUID por captura. `situacao` e `dataMovimentacao` não viram coluna no MVP (“Pendente” = `data_audiencia >= agora`).
2. **Ciclo de 10 min:** união de `cdProcesso` de intimações + audiências + processos **já persistidos** daquele advogado; ficha via `GET /api/processos?cdsProcesso=...`; código omitido no 200 = skip, não falha o lote. **Carteira completa** (“todos os processos” do PRD) é importação à parte, quando o Network da home `tarefas-adv` revelar outra lista — não bloqueia os pipes de monitoramento.
3. **Movimentações:** só depois de uma captura CPO com `movimentacoes` preenchido e parser que ignore cabeçalho de tabela. Segredo de justiça = pular CPO, sem senha de autos. Enquanto isso o ciclo pode ser intimação + audiência + upsert da ficha.
4. **`GET /tarefas-adv/api/peticoes` fora do ciclo.** Não misturar com `movimentacoes`. Petição nos autos, se existir no CPO, cai no pipe de movimentações. “Aguardando assinatura” só entra com tabela/`cdProtocolo` se o produto pedir.

## Alternativas consideradas

- Unique SQL `(user_id, cd_processo, data_audiencia, titulo)` com coluna nova: mais limpo, mas migration agora sem ganho — o `id_esaj` composto reusa o unique existente.
- UUID por audiência a cada poll: duplicaria o diff.
- Esperar lista completa da carteira antes de qualquer pipe: atrasaria intimação/audiência, que já têm contrato.
- Inventar movimentação a partir de `peticoes_diversas` do CPO: bloco sujo (header-as-row), outro significado.
- Manter `pipe_peticoes` no intervalo de 10 min como no PRD: o JSON real não é andamento processual.

## Consequências

- Etapa 7 começa por intimação → audiência (id composto) → upsert de ficha; CPO só com fixture boa.
- Processos sem intimação/audiência recente e ainda não persistidos ficam de fora até a importação da carteira.
- Comentário do PRD sobre quatro pipes paralelos incluindo petições fica desatualizado — a fonte de verdade é `/docs/modulos/esaj-apis.md`.
