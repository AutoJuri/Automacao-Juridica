# Índice de Documentação — Automação Jurídica

> Leia este arquivo primeiro em qualquer conversa nova sobre o projeto.
> Ele é a fonte de verdade sobre arquitetura, padrões e decisões tomadas.

---

## Stack Técnica

- **Frontend:** React + TypeScript + Vite + TanStack Router + TanStack Query + Axios + Zustand + Tailwind + shadcn/ui (Bun)
- **Backend:** Python 3.12 + FastAPI + Uvicorn + SQLAlchemy 2.0 async + Alembic + APScheduler (UV)
- **Scraping:** Playwright (login e-SAJ, headless, Etapa 6+) + httpx (APIs internas) + BeautifulSoup4 (HTML)
- **Banco:** PostgreSQL no Railway
- **Criptografia:** AES-256-GCM via `cryptography` lib (Etapa 5+)
- **Integrações:** Gmail API (Google) e Microsoft Graph API (Outlook) via OAuth2 (Etapa 5+, httpx puro, com `refresh_access_token` desde a Etapa 6), DataJud CNJ (gratuito, próxima etapa)
- **Infra:** Monorepo (frontend/ + backend/), Dockerfile, Railway

---

## Padrões Globais do Projeto

- `user_id` **sempre** vem do JWT validado — nunca do body, query ou path param
- Toda query que acessa dado de advogado verifica `WHERE user_id = current_user.id` **no banco**
- Todo endpoint protegido usa `Depends(get_current_user)` — sem exceção
- Todo endpoint FastAPI usa `ResponseSchema` Pydantic — nunca retorna ORM diretamente
- Credenciais e cookies do e-SAJ criptografados com AES-256-GCM (`encrypt_secret`/`decrypt_secret`) — descriptografar **só em memória**
- CPF nunca é decriptado para exibição — coluna `cpf_mascarado` calculada uma vez no cadastro (ADR-005)
- `state` de fluxos OAuth2 é JWT assinado stateless, nunca tabela de sessão (ADR-006)
- `TribunalSession.cookie_encrypted` é nullable — só preenchido após 1º login bem-sucedido (ADR-007)
- Validação de credencial roda em `BackgroundTask` + polling do frontend, nunca síncrona na resposta do cadastro (ADR-008)
- Captura do código MFA usa `SessionLocal` própria — nunca a mesma sessão do orquestrador Playwright (ADR-009)
- Pipes e-SAJ: `id_esaj` de audiência é composto; petições `tarefas-adv` fora do ciclo; CPO só com fixture de movimentações (ADR-010)
- Payload bruto do e-SAJ: validar **item a item** (`validar_itens`); item inválido é omitido; log só tipo do erro + nome do campo — nunca o input (OAB no `id` da intimação)
- `titulo` / `local` / `id_esaj` cabem em `VARCHAR(255)`: truncar no ETL, não alargar coluna agora
- Depois de `gerar_notificacoes`, marcar intimação/audiência nova com `is_new=False` — a notificação já foi emitida
- Scheduler: `CronTrigger`/`AsyncIOScheduler` sempre com `timezone=America/Sao_Paulo` explícito — o host roda em UTC (ADR-011)
- Scheduler **off** em `APP_ENV=development` (override `SCHEDULER_ENABLED=true`); em produção liga sozinho
- Rate limit (429) nos pipes vira `bloqueado` com backoff, sem invalidar o cookie — só sessão inválida/erro de login zera o cookie (ADR-011)
- `reauth_pendente` e cookie `ativo` expirado disparam reauth no próximo tick de 10 min; duplicata de Playwright no mesmo processo é barrada por `_VALIDACOES_EM_ANDAMENTO` (fecha o gap da ADR-008)
- Contexto Playwright **isolado por advogado** — nunca compartilhado, sempre headless em produção
- Logs **nunca** contêm CPF, senha, cookie ou token OAuth2
- IDs são sempre **UUID** — nunca sequenciais
- Senhas da plataforma com **bcrypt** (mínimo 12 rounds)
- JWT: access token (~15 min) só em memória (Zustand); refresh (~7 dias) em cookie HttpOnly + Secure + SameSite=Strict
- Refresh token no banco só como **hash SHA-256**; rotacionado a cada `/auth/refresh`
- Sessão da SPA: restore silencioso no boot via `ensureSessionRestored()` (ADR-004)
- CORS aceita **apenas** a origem do frontend em produção — nunca `allow_origins=["*"]`
- `DATABASE_URL` do `.env` pode ser a URL crua do Railway; use sempre `settings.sqlalchemy_url` (ADR-001)
- Estados de domínio (`status`, `tipo`) são `VARCHAR` + constantes Python — sem ENUM nativo (ADR-002)
- Consulte `security.mdc` para diretrizes completas de segurança
- Consulte `PRD.md` para requisitos e regras de negócio

---

## Ciclo de Coleta (referência rápida)

```
Às 1h da manhã (America/Sao_Paulo) → cron renova cookie de todo advogado com credencial ativa
A cada 10 minutos → por advogado: Playwright em andamento → skip | ativo + cookie ok → pipes | ativo + cookie expirado / reauth_pendente → reauth | bloqueado + backoff passou → pipes | senão → espera
                  → intimação (menu Manifestações/ciência) → audiência → upsert da ficha
                  → CPO/movimentações só com fixture; petições (Assinar e enviar) fora do ciclo
                  → ETL normaliza → Diff compara → Notificação se mudou
```

Contrato e validação ao vivo: `/docs/modulos/esaj-apis.md` (ADR-010). Scheduler e decisão por advogado: `/docs/modulos/scheduler.md` (ADR-011).

`GET /credentials/status` inclui `sessao_expirada` (cookie `ativo` fora das ~22h) — a UI mostra Revalidar só nesse caso.

**Status do advogado (`tribunal_sessions.status`):**
- `ativo` — funcionando normalmente
- `reauth_pendente` — cookie expirou, reautenticando
- `bloqueado` — rate limit ativo
- `credencial_invalida` — advogado trocou senha no e-SAJ
- `email_desconectado` — OAuth2 do email expirou
- `portal_indisponivel` — e-SAJ fora do ar
- `codigo_nao_encontrado` — e-mail conectado, mas o código MFA não chegou a tempo

---

## Estrutura do Monorepo

```
automacao-juridica/
├── frontend/                  → React + Bun
│   └── src/
│       ├── features/
│       │   ├── auth/
│       │   ├── processos/
│       │   ├── notificacoes/
│       │   └── settings/
│       ├── store/             → Zustand (auth em memória)
│       └── routes/            → TanStack Router
│
├── backend/                   → FastAPI + UV
│   └── app/
│       ├── api/               → Rotas FastAPI
│       ├── services/          → Lógica de negócio
│       │   └── pipes/         → Coleta por tipo
│       ├── models/            → SQLAlchemy models
│       ├── schemas/           → Pydantic schemas
│       ├── core/              → JWT, AES-256, APScheduler, config
│       └── db/                → Sessão async + Alembic migrations
│
└── docs/
    ├── INDEX.md               → Este arquivo
    ├── PRD.md                 → Requisitos e arquitetura de produto
    ├── modulos/               → Documentação por módulo
    └── decisions/             → ADRs (decisões arquiteturais)
```

---

## Módulos Documentados

| Módulo | Camada | Arquivo | Status |
|---|---|---|---|
| Migrations e Camada de Dados | Infra / Backend | `/docs/modulos/migrations.md` | Completo |
| Autenticação da Plataforma | Backend / Frontend | `/docs/modulos/auth.md` | Completo |
| Credenciais do e-SAJ e Conexão de E-mail (OAuth2) | Backend / Frontend | `/docs/modulos/credenciais-esaj-email.md` | Completo |
| Login Automatizado no e-SAJ (Playwright) | Backend | `/docs/modulos/login-esaj.md` | Completo |
| Contrato das APIs internas do e-SAJ (TJSP) | Backend / Scraping | `/docs/modulos/esaj-apis.md` | Completo (pipes + hardening 2026-08-21) |
| Scheduler e Ciclo Automático | Backend | `/docs/modulos/scheduler.md` | Completo (Etapa 8 + hardening 2026-08-21) |

---

## Decisões Arquiteturais (ADRs)

| Número | Decisão | Arquivo |
|---|---|---|
| ADR-001 | Normalização da DATABASE_URL do Railway para asyncpg | `/docs/decisions/001-normalizacao-database-url-railway.md` |
| ADR-002 | VARCHAR + constantes Python em vez de ENUM nativo do Postgres | `/docs/decisions/002-varchar-em-vez-de-enum-postgres.md` |
| ADR-003 | Recuperação de senha via log (sem provedor de e-mail ainda) | `/docs/decisions/003-recuperacao-senha-via-log.md` |
| ADR-004 | Restauração silenciosa de sessão no boot da SPA | `/docs/decisions/004-bootstrap-sessao-spa.md` |
| ADR-005 | Mascaramento de CPF sem decriptação (coluna `cpf_mascarado` em texto puro) | `/docs/decisions/005-mascaramento-cpf-sem-decriptacao.md` |
| ADR-006 | `state` do OAuth2 como JWT assinado stateless | `/docs/decisions/006-oauth-state-jwt-stateless.md` |
| ADR-007 | `TribunalSession.cookie_encrypted` nullable | `/docs/decisions/007-cookie-encrypted-nullable.md` |
| ADR-008 | Validação de credenciais em background task + polling do frontend | `/docs/decisions/008-validacao-background-polling.md` |
| ADR-009 | Sessão SQLAlchemy dedicada para captura do código MFA | `/docs/decisions/009-sessao-dedicada-captura-email.md` |
| ADR-010 | Contrato dos pipes e-SAJ (id de audiência, carteira, CPO, petições) | `/docs/decisions/010-contrato-pipes-esaj.md` |
| ADR-011 | Timezone explícito no scheduler, rate limit sem invalidar cookie, `reauth_pendente` no próximo tick | `/docs/decisions/011-scheduler-timezone-e-rate-limit.md` |

---

## Backlog

| Backlog | Origem | Arquivo |
|---|---|---|
| Hardening de Auth (itens 7+) | Code review das Etapas 3–4 | `/docs/backlog-auth-hardening.md` |
| Hardening Credenciais / Login e-SAJ | Code review das Etapas 5–6 | `/docs/backlog-credentials-login-hardening.md` |
| Hardening Pipes / Scheduler | Code review das Etapas 7–8 | `/docs/backlog-pipes-scheduler-hardening.md` |
