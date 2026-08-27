# ADR-013: CPO enriquece a ficha; JSON continua fonte de classe, polos, intimações e agenda

**Data:** 2026-08-25
**Status:** Aceito

---

## Contexto

O GET JSON de processos (`/tarefas-adv/api/processos`) já alimenta classe, assunto, polos e URLs da ficha. Intimações e a agenda de audiências da carteira vêm das APIs JSON correspondentes. O HTML do CPO (`GET /cpopg/show.do`) já era baixado no lote de 5 da `pipe_movimentacoes` só para o histórico de andamentos (ADR-012).

Capturas posteriores (gitignoradas) mostraram que a **mesma página** traz capa complementar (foro, vara, juiz, distribuição, controle, área, valor da ação), lista completa de partes, petições diversas, audiências daquele processo e empty states de incidentes/apensos — campos que o JSON da carteira não entrega. Abrir um segundo pipe HTTP seria custo duplicado: o HTML já está no ciclo.

## Decisão

1. **Sem pipe HTTP nova.** O parse do CPO no lote existente passa a preencher capa, partes, petições diversas, audiências da página e flags de empty state, além das movimentações. `Processo.movimentacoes_synced_at` continua sendo o throttle de **todo** o HTML do CPO.
2. **JSON não é sobrescrito.** `de_classe`, `de_assunto`, `parte_ativa` / `parte_passiva`, intimações e a tabela `audiencias` (agenda da carteira) seguem sendo a fonte. O CPO não grava nesses campos.
3. **Audiência CPO ≠ agenda JSON.** A tabela `audiencias_cpo` é própria. A UI mostra os dois blocos no detalhe; não misturar linhas.
4. **Petições diversas do CPO ≠ `GET /api/peticoes`.** A API JSON de petições continua fora do ciclo (ADR-010, rascunhos “Assinar e enviar”). Linhas do bloco “Petições diversas” da capa vão para `peticoes_diversas`, com unique estável (protocolo quando existir; senão hash `data|tipo|texto_extra`).
5. **`requer_senha_processo=True`:** não gravar capa, partes, petições nem audiências CPO — igual às movimentações. Nunca pedir ou guardar senha dos autos.
6. **Incidentes/apensos:** só flags booleanas de empty state (`sem_incidentes` / `sem_apensos`; `None` = CPO ainda não passou). Sem modelar vínculo processo→processo.
7. **Sem `Notification` nova** para petição diversa ou audiência CPO — backfill do lote geraria ruído. Movimentações novas continuam notificando (ADR-012).
8. **API pública:** os campos novos saem só no detalhe (`GET /processos/{id}`). A lista da home e o card não mudam. Texto, nunca HTML; sem `id_esaj` / `identidade_hash`.

Fora desta etapa: histórico de classes, linhas preenchidas de incidentes/apensos, bloco CDA, PDF.

## Alternativas consideradas

- Pipe HTTP nova só para capa: descartada — o fetch já existe no lote de movimentações.
- Sobrescrever classe/assunto/polos com o CPO: descartada — o JSON da carteira já é a fonte estável do card e da busca.
- Gravar audiências do CPO em `audiencias`: descartada — semântica diferente (agenda da carteira vs. tabela da capa daquele processo) e unique/`id_esaj` compostos do JSON não se aplicam.
- Notificar petição/audiência CPO: descartada — o primeiro ciclo de um processo antigo dispararia dezenas de alertas de backfill.

## Consequências

- Parser (`esaj_cpo_parser`) e `CpoDetalheRaw` expandem capa/partes/petições/audiências CPO/flags.
- Colunas novas em `processos` + tabelas `peticoes_diversas` e `audiencias_cpo`.
- O mesmo loop de `_coletar_movimentacoes` persiste os blocos (savepoint por processo).
- O detalhe da SPA ganha metadados, lista de partes CPO, bloco de audiências CPO, petições diversas e empty states de incidentes/apensos. O card da home permanece polo JSON.
