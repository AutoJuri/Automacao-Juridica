# Backlog — Hardening Pipes / Scheduler

Origem: code review das Etapas 7–8 (2026-08-21).

Itens 1–6 do review e as melhorias simples (testes, `is_new=False` após notificar, remoção de `TAREFAS_ADV_PATH`) foram implementados no hardening. Restam só decisões de produto/infra.

---

## Aberto

1. **Portal 5xx nos pipes não muda `tribunal_sessions.status`.** A sessão fica `ativo` e o próximo tick de 10 min tenta de novo. Alinhar com o login (`portal_indisponivel`) implicaria pular o restante da carteira no mesmo ciclo — decisão de produto, não bug. Ver tabela de erros em `docs/modulos/scheduler.md`.

2. **Lock de validação/scheduler por `user_id` no banco** quando houver múltiplos workers. O guard `_VALIDACOES_EM_ANDAMENTO` só cobre o processo atual (já está no backlog de credenciais; o scheduler herda o mesmo limite da ADR-008).

3. **Ampliar `id_esaj` / `titulo` / `local` via migration** se o truncate de 255 no ETL (`TITULO_MAX` / `ID_ESAJ_MAX`) começar a colidir na prática (duas audiências distintas caindo na mesma chave composta). Sem evidência disso nas capturas atuais.

4. **Scripts de smoke (`disparar_coleta.py` e afins) imprimem CNJ/título.** Já documentado; não colar a saída no Git. Nada a mudar no código.

5. **Busca `q` da lista de processos:** escapar `%`/`_` no `ILIKE` e incluir `parte_passiva["nome"]` (hoje só `parte_ativa`).

6. **Testes de integração de ownership** com Postgres efêmero nas rotas `/processos` e `/notifications` (hoje `test_painel` mocka o service).

7. **Teto do ciclo CPO vs timeout:** 5 fetches HTML × 20s podem estourar os 60s do ciclo com portal lento — reduzir lote, timeout por HTML ou orçamento residual.

8. **Truncar `descricao` na API pública** (intimação/movimentação) para não devolver payloads enormes do scraping.
