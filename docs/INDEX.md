# Índice de Documentação — Automação Jurídica

> Leia este arquivo primeiro em qualquer conversa nova sobre o projeto.
> Ele é a fonte de verdade sobre arquitetura, padrões e decisões tomadas.

---

## Stack Técnica

- **Frontend:** React + TypeScript + Vite + TanStack Router + TanStack Query + Axios + Zustand + Tailwind + shadcn/ui (Bun)
- **Backend:** Python 3.12 + FastAPI + Uvicorn + SQLAlchemy 2.0 async + Alembic + APScheduler (UV)
- **Scraping:** Playwright (login e-SAJ) + httpx (APIs internas) + BeautifulSoup4 (HTML)
- **Banco:** PostgreSQL no Railway
- **Criptografia:** AES-256 via `cryptography` lib (Etapa 3+)
- **Integrações:** Gmail API (Google), Microsoft Graph API (Outlook), DataJud CNJ (gratuito)
- **Infra:** Monorepo (frontend/ + backend/), Dockerfile, Railway

---

## Padrões Globais do Projeto

- `user_id` **sempre** vem do JWT validado — nunca do body, query ou path param
- Toda query que acessa dado de advogado verifica `WHERE user_id = current_user.id` **no banco**
- Todo endpoint protegido usa `Depends(get_current_user)` — sem exceção
- Todo endpoint FastAPI usa `ResponseSchema` Pydantic — nunca retorna ORM diretamente
- Credenciais e cookies do e-SAJ criptografados com AES-256 — descriptografar **só em memória**
- Contexto Playwright **isolado por advogado** — nunca compartilhado
- Logs **nunca** contêm CPF, senha, cookie ou token OAuth2
- IDs são sempre **UUID** — nunca sequenciais
- Senhas da plataforma com **bcrypt** (mínimo 12 rounds)
- CORS aceita **apenas** a origem do frontend em produção — nunca `allow_origins=["*"]`
- `DATABASE_URL` do `.env` pode ser a URL crua do Railway; use sempre `settings.sqlalchemy_url` (ADR-001)
- Estados de domínio (`status`, `tipo`) são `VARCHAR` + constantes Python — sem ENUM nativo (ADR-002)
- Consulte `security.mdc` para diretrizes completas de segurança
- Consulte `PRD.md` para requisitos e regras de negócio

---

## Ciclo de Coleta (referência rápida)

```
Às 1h da manhã   → Playwright renova cookie de sessão por advogado
A cada 10 minutos → 4 pipes paralelos por advogado (intimações, audiências, petições, processos)
                  → ETL normaliza → Diff compara → Notificação se mudou
```

**Status do advogado (`tribunal_sessions.status`):**
- `ativo` — funcionando normalmente
- `reauth_pendente` — cookie expirou, reautenticando
- `bloqueado` — rate limit ativo
- `credencial_invalida` — advogado trocou senha no e-SAJ
- `email_desconectado` — OAuth2 do email expirou
- `portal_indisponivel` — e-SAJ fora do ar

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

---

## Decisões Arquiteturais (ADRs)

| Número | Decisão | Arquivo |
|---|---|---|
| ADR-001 | Normalização da DATABASE_URL do Railway para asyncpg | `/docs/decisions/001-normalizacao-database-url-railway.md` |
| ADR-002 | VARCHAR + constantes Python em vez de ENUM nativo do Postgres | `/docs/decisions/002-varchar-em-vez-de-enum-postgres.md` |
