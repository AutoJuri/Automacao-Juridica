# Módulo: Deploy (Railway)

> Última atualização: 2026-09-15
> Camada: Infra

---

## O que este módulo faz

Empacota o backend FastAPI (API + APScheduler + Chromium do Playwright) para o Railway, aplica as migrations no pre-deploy e deixa explícito quais variáveis o serviço precisa — sem commitar segredo. O Postgres do projeto já vive no Railway; este módulo é o serviço da **API**. O frontend é outro serviço (ou outro host) com `VITE_API_URL` apontando para a URL HTTPS desta API.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/Dockerfile` | Imagem: UV pinado por digest, Playwright Chromium, Uvicorn em `$PORT` |
| `backend/railway.toml` | Referência (healthcheck `/health`, 1 réplica, Alembic no pre-deploy) — serviço novo pode ignorar; copiar na UI |
| `backend/.env.production.example` | **Nomes** das variáveis do painel — sem valores reais |
| `backend/.env.example` | Molde do `.env` **local** (`APP_ENV=development`) |
| `backend/.dockerignore` | Não copia `.env`, testes nem `.venv` para a imagem |

---

## Endpoints

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/health` | Liveness do processo. Healthcheck do Railway usa **só** esta rota | Não |
| GET | `/health/db` | `SELECT 1` no Postgres — checagem **manual** depois do deploy | Não |

`/docs`, `/redoc` e `/openapi.json` existem **somente** com `APP_ENV=development`.

> Rotas de negócio (`/auth`, `/processos`, …) estão nos módulos respectivos.
> `user_id` nunca é aceito via body ou query — sempre vem do JWT.

---

## Checklist para quem vai criar o serviço (Railway)

O `railway.toml` é referência. **Preencha sempre no painel** (serviço novo pode ignorar o arquivo):

1. No **mesmo projeto** do Postgres, New → GitHub (este repo).
2. **Obrigatório na UI (Settings):**
   - Root Directory = `backend`
   - Builder = Dockerfile
   - Healthcheck path = `/health`
   - Pre-deploy command = `uv run alembic upgrade head`
   - Replicas = 1
3. **Variables** — só o que está em `.env.production.example`. Obrigatório:
   - `APP_ENV=production`
   - `DATABASE_URL` → **Add a reference** da `DATABASE_URL` do plugin Postgres (rede interna). Não use `DATABASE_PUBLIC_URL` neste serviço.
   - `JWT_SECRET` e `AES_KEY` — gerar com `python -c "import secrets; print(secrets.token_urlsafe(48))"` (dois valores **diferentes**, ≥ 32 caracteres). Nunca os `change-me-…` do example local.
   - `CORS_ORIGINS` — URL HTTPS do frontend, **sem** barra no final.
4. Generate domain no serviço da API.
5. Depois do primeiro deploy: conferir no **log do pre-deploy** que o Alembic rodou; `https://<api>/health` e `https://<api>/health/db` devem responder `ok`.
6. OAuth (Gmail/Outlook) e `DATAJUD_API_KEY` podem ficar vazios no primeiro ar. Sem OAuth, o advogado **não** conecta o e-mail do e-SAJ. Sem a chave, o job DataJud não consulta (só loga e sai).
7. Memória: reserve folga (~1 GB) por causa do Chromium.

Não cole `backend/.env` (development) no painel. Não commite `JWT_SECRET` / `AES_KEY`.

---

## Cookie e CORS

O refresh token vai em cookie `HttpOnly` + `SameSite=Strict` + `Path=/auth`.

- `https://app.dominio.com` + `https://api.dominio.com` → mesmo site → o cookie **é** enviado.
- Dois `*.up.railway.app` diferentes → o browser trata como sites diferentes → login some no F5.

`CORS_ORIGINS` tem que ser exatamente a origem do front (nunca `*`).

---

## Frontend (outro serviço)

Build com `VITE_API_URL=https://<url-da-api>` **no momento do `bun run build`**. Mudou a URL da API → rebuild. Única variável `VITE_*` permitida.

---

## Jobs

Com `APP_ENV=production` o APScheduler **liga sozinho** (pipes a cada 10 min, cookie às 1h Brasília, DataJud diário se houver chave). Para subir a API sem jobs: `SCHEDULER_ENABLED=false`.

Recuperação de senha **não** envia e-mail em produção até existir provedor (ADR-003).

Chromium no container: `playwright.chromium.launch` usa `--no-sandbox` e `--disable-dev-shm-usage` (non-root + `/dev/shm` pequeno). Isolamento continua sendo um contexto Playwright novo por advogado.

---

## Padrões seguidos neste módulo

- Segredos só no painel do Railway — nunca `COPY .env` na imagem
- Processo **não-root** (`USER appuser`)
- Chromium via `playwright install`, path `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`
- Uvicorn escuta `PORT` (Railway) com fallback 8000
- Migrations no **pre-deploy**, não no `CMD` (e conferidas no log — o `railway.toml` pode não aplicar)
- Healthcheck `/health` (liveness). `/health/db` para checar Postgres depois
- UV na imagem pinado por digest SHA-256, não `latest`

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| Migrations | `uv run alembic upgrade head` no pre-deploy |
| Autenticação | Cookie `SameSite=Strict` + `CORS_ORIGINS` da origem real do front |
| Login e-SAJ | Chromium do Playwright na imagem; flags de container no `launch` |
| Scheduler | Com `APP_ENV=production` os jobs ligam sozinhos |

---

## O que NÃO fazer aqui

- ❌ Não usar `DATABASE_PUBLIC_URL` no serviço da API (só no `.env` da máquina local)
- ❌ Não deixar `APP_ENV=development` no Railway (cookie sem `Secure`; aceita JWT/AES placeholder)
- ❌ Não escalar réplicas sem Redis no rate limiter
- ❌ Não instalar só o `chromium` do apt — o Playwright não o encontra
- ❌ Não lançar o Chromium no Docker sem `--no-sandbox` e `--disable-dev-shm-usage`
- ❌ Não assumir que o `railway.toml` aplicou sozinho — preencher a UI e conferir o log do Alembic
- ❌ Não bake `VITE_*` secretos no frontend

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-09-15 | Dockerfile com Playwright Chromium + `$PORT`; `railway.toml` (healthcheck, 1 réplica, Alembic no pre-deploy); `.env.production.example` só com nomes |
| 2026-09-15 | Review: UV por digest; `/docs` só em development; checklist da UI obrigatório; Chromium com flags de container; seções Endpoints/Dependências |
