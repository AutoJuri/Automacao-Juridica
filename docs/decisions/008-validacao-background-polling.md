# ADR-008: Validação de credenciais em background task + polling do frontend

**Data:** 2026-08-13 (atualizado 2026-08-21: gap de `reauth_pendente` órfão fechado pelo scheduler, ADR-011)
**Status:** Aceito

---

## Contexto

`POST /credentials/esaj` precisa, na Etapa 6, além de salvar CPF/senha criptografados, também **validar** essas credenciais fazendo um login real no e-SAJ (Playwright: preencher formulário, aguardar e capturar o código de duplo fator por e-mail, aquecer a sessão, extrair cookies). Esse fluxo completo pode levar até a casa de 40-60 segundos — o código de verificação por e-mail sozinho pode demorar até ~40s para chegar e ser encontrado via polling na API do Gmail/Outlook.

Uma requisição HTTP síncrona de formulário (`POST /credentials/esaj` esperando o login terminar antes de responder) deixaria o navegador do advogado "pendurado" por até um minuto, sem nenhum feedback incremental, arriscando timeout do proxy/browser e uma UX ruim logo no primeiro cadastro.

## Decisão

`POST /credentials/esaj` continua respondendo imediatamente após salvar a credencial (como já fazia antes da Etapa 6), e dispara `validar_credencial_esaj(user_id)` como uma `BackgroundTask` do FastAPI — a validação real roda depois da resposta HTTP ter sido enviada, no mesmo processo. O frontend passa a consultar `GET /credentials/status` em polling (a cada 3s, via `refetchInterval` do TanStack Query) enquanto `session_status` for `None` ou `reauth_pendente`, e para de fazer polling assim que chegar a um status terminal (`ativo` ou qualquer status de falha). Um novo endpoint `POST /credentials/esaj/revalidar` permite disparar uma nova tentativa sem reenviar CPF/senha (ex.: depois de conectar o e-mail, ou quando o e-SAJ estava fora do ar).

## Alternativas consideradas

- **Resposta síncrona, aguardando o login terminar:** rejeitada pelo motivo acima — tempo de resposta inaceitável e risco de timeout de proxy/browser.
- **WebSocket ou Server-Sent Events para notificar o frontend em tempo real:** resolveria o polling, mas introduz um canal de comunicação novo (conexão persistente, reconexão, autenticação sobre WS) para um caso de uso que ocorre raramente (só no cadastro/revalidação, não em uso contínuo) — desproporcional neste estágio do projeto.
- **Fila de jobs dedicada (Celery/RQ + Redis) em vez de `BackgroundTasks` do FastAPI:** `BackgroundTasks` roda no mesmo processo/worker que atendeu a requisição, o que é uma limitação real (não sobrevive a um restart do processo, não escala para múltiplos workers de forma coordenada), mas é suficiente para o volume esperado do projeto nesta fase e evita adicionar Redis/Celery só para este fluxo. Fica registrado como possível evolução futura se o volume de advogados justificar.

## Consequências

- O guard `_VALIDACOES_EM_ANDAMENTO` (em `credential_validation.py`) só protege contra execuções concorrentes **dentro do mesmo processo** — múltiplos workers do Uvicorn/Gunicorn poderiam, em teoria, rodar duas validações do mesmo advogado ao mesmo tempo. Aceitável por ora (o pior resultado é um dos dois logins "perder" a corrida e sobrescrever o status do outro, sem corrupção de dado), mas deve ser revisitado se o projeto migrar para múltiplos workers em produção.
- Se o processo reiniciar no meio de uma validação, a `TribunalSession` fica presa em `reauth_pendente` até o próximo `job_ciclo_dez_minutos` — o scheduler chama `validar_credencial_esaj` no tick (ADR-011, hardening 2026-08-21). Duplicata no mesmo processo continua barrada por `_VALIDACOES_EM_ANDAMENTO`. Múltiplos workers continuam fora do escopo (mesmo limite desta ADR).
- O frontend nunca deve tratar "resposta 200 de `POST /credentials/esaj`" como "credencial validada" — só `session_status === "ativo"` (obtido via polling) significa que o login de fato funcionou.
- Abre caminho direto para a Etapa 7 (APScheduler): o mesmo `validar_credencial_esaj` será reaproveitado tanto pelo cron diário de reautenticação quanto por qualquer disparo manual futuro.
