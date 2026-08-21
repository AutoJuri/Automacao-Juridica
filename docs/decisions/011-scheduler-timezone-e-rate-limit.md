# ADR-011: Timezone explícito no scheduler, rate limit sem invalidar cookie e reauth de `reauth_pendente` no próximo tick

**Data:** 2026-08-21 (hardening no mesmo dia: reauth no tick, cookie expirado, choque 1h)
**Status:** Aceito

---

## Contexto

A Etapa 8 pediu para integrar o APScheduler ao FastAPI com dois jobs (renovação de cookie às 1h da manhã, ciclo de pipes a cada 10 min), tratamento de erro por tipo (rate limit, cookie expirado, portal fora do ar), status por advogado e job logs — além de resolver "a questão do timezone". Três decisões de design não estavam explícitas no PRD e precisaram ser tomadas durante a implementação:

1. O Railway roda o container em UTC. Um `CronTrigger(hour=1)` sem timezone explícito dispara à 1h **UTC**, que é 22h em Brasília — não "1h da manhã" como o PRD descreve.
2. O PRD pede backoff específico para rate limit (429) — "5min → 15min → 60min → pula o ciclo" — mas até a Etapa 7 os pipes de coleta (`app/services/esaj_http.py`) tratavam qualquer status HTTP diferente de 200 (exceto redirect de login) como o mesmo erro genérico `EsajPortalIndisponivelError`, sem backoff dedicado.
3. A ADR-008 já registrava um gap conhecido: se o processo reiniciar no meio de uma validação de credencial, a `TribunalSession` fica presa em `reauth_pendente` para sempre, porque nada revisita esse estado — e a própria ADR-008 apontava a "Etapa 7 [scheduler]" como o momento de resolver isso.

## Decisão

**Timezone:** o `AsyncIOScheduler` e o `CronTrigger` do job diário recebem `timezone=ZoneInfo("America/Sao_Paulo")` explicitamente (`app/core/scheduler.py`). Não depende da timezone do SO/container.

**Rate limit dedicado:** `esaj_http.buscar_json` levanta `EsajRateLimitError` quando o e-SAJ responde 429, distinta de `EsajPortalIndisponivelError`. Em `coleta_esaj._coletar_pipe`, esse erro marca `TribunalSession.status = bloqueado`, incrementa `tentativas_falha` e calcula `proximo_retry` (mesma tabela de backoff do login: 5→15→60min) — **sem** anular o cookie, porque rate limit não significa sessão inválida. `job_ciclo_dez_minutos` (`app/services/scheduler_jobs.py`), ao encontrar uma sessão `bloqueado` cujo `proximo_retry` já passou, volta o status para `ativo` (mantendo o cookie) e tenta os pipes de novo direto — sem passar pelo Playwright.

**Backoff compartilhado:** `calcular_proximo_retry` foi extraído de `credential_validation.py` para `app/core/backoff.py`, reaproveitado tanto pela falha de login quanto pelo rate limit dos pipes — mesma escala de espera, porque o recurso limitado do outro lado (e-SAJ) é o mesmo nos dois casos.

**`reauth_pendente`:** `job_ciclo_dez_minutos` chama `validar_credencial_esaj` no mesmo tick, sem espera. Duplicata no mesmo processo é barrada por `_VALIDACOES_EM_ANDAMENTO` (`credential_validation.py`). Depois de um restart, a sessão órfã (gap da ADR-008) é retentada na hora — não há mais limiar de 5 minutos (`REAUTH_PENDENTE_STALE_MINUTOS` foi removido).

**Cookie expirado em sessão `ativo`:** se `cookie_expirado()` é verdadeiro, o tick dispara reauth e **não** entra nos pipes. O mesmo guard existe em `executar_ciclo_usuario` para scripts manuais.

**Choque 1h:** se `validacao_em_andamento(user_id)` (Playwright já rodando para aquele advogado), o ciclo de 10 min pula aquele advogado — o cookie pode estar sendo anulado agora.

**Rótulo do `JobLog`:** `validar_credencial_esaj` ganhou o parâmetro `job_tipo: str = JOB_TIPO_LOGIN`. O cron noturno passa `job_tipo=JOB_TIPO_REAUTH`; os disparos do próprio advogado (`POST /credentials/esaj`, `POST /credentials/esaj/revalidar`) continuam com o default `login`. A lógica de validação é idêntica — só o registro em `job_logs` muda, para permitir distinguir renovação automática de ação manual na auditoria.

## Alternativas consideradas

- **Deixar o rate limit cair no mesmo `erro_portal` genérico, sem backoff dedicado:** mais simples, mas não fecha o requisito explícito do PRD ("backoff exponencial: 5min → 15min → 60min") e arrisca martelar o e-SAJ a cada 10 minutos durante um bloqueio, piorando o próprio rate limit.
- **Terceiro job dedicado a "retry de reautenticação" a cada poucos minutos:** resolveria a reautenticação imediata do PRD ("se cookie inválido → agenda reautenticação imediata"), mas o usuário pediu explicitamente "os dois jobs". A decisão do sistema por sessão dentro de `job_ciclo_dez_minutos` (pipes vs. reauth vs. esperar) cobre o mesmo requisito sem um terceiro cron. Duplicata de Playwright no mesmo processo já é barrada por `_VALIDACOES_EM_ANDAMENTO`.
- **Limiar de 5 min (`REAUTH_PENDENTE_STALE_MINUTOS`) para não duplicar validação:** descartado no hardening pós-review das Etapas 7–8. O set em memória cobre o “validação ainda rodando”; o stale atrasava o retry após restart e deixava o gap da ADR-008 aberto por até 5 minutos.
- **Horários configuráveis via variável de ambiente (`SCHEDULER_REAUTH_HOUR`, etc.):** decisão consciente de manter como constante fixa no código, mesmo padrão já usado em `TIMEOUT_VALIDACAO_SEGUNDOS` — simplicidade preferida sobre flexibilidade não solicitada.
- **Resolver o `reauth_pendente` travado com um job de limpeza dedicado:** desproporcional para o volume esperado — a verificação já acontece de qualquer forma a cada 10 minutos dentro de `job_ciclo_dez_minutos`, então um job separado só duplicaria a leitura da mesma tabela.

## Consequências

- `AsyncIOScheduler`/`CronTrigger`/`IntervalTrigger` (pacote `apscheduler` v3, `apscheduler>=3.10,<4`) entram como dependência real do backend.
- `tribunal_sessions.status = bloqueado` agora tem dois caminhos possíveis para chegar lá: falha de login com muitas tentativas (já existia) e rate limit direto nos pipes (novo) — os dois usam a mesma tabela de backoff, então o comportamento observável pelo advogado (tempo de espera) é consistente independente da causa.
- `job_ciclo_dez_minutos` decide, por advogado, se roda pipes ou reauth — isso significa que qualquer novo status de erro adicionado a `SESSION_STATUSES` no futuro precisa ser explicitamente incluído em `_STATUS_ELEGIVEIS_PARA_REAUTH` (ou em outro branch) em `scheduler_jobs.py`, senão fica "esquecido" e nunca mais é retentado automaticamente.
- O guard `_VALIDACOES_EM_ANDAMENTO` (nível de processo, ADR-008) continua sendo a única proteção contra duas validações concorrentes do mesmo advogado — o scheduler não adiciona um lock de banco. Múltiplos workers em produção continuam fora do escopo (mesma ressalva da ADR-008). `validacao_em_andamento(user_id)` é o mesmo set, lido pelo ciclo de 10 min para não disparar pipes durante o Playwright.
- O logger do `httpx` (que expunha a URL completa, incluindo `cdsProcesso`, em nível INFO) foi rebaixado para `WARNING` em `app/services/esaj_http.py` como parte desta etapa, fechando uma pendência de segurança que estava documentada em `docs/modulos/esaj-apis.md`.
