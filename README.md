# Automação Jurídica

Monorepo do MVP: painel web + backend FastAPI para monitoramento automatizado de processos no e-SAJ (TJSP).

```
automacao-juridica-web/
├── frontend/     # React + TypeScript + Bun + TanStack Router + shadcn
├── backend/      # FastAPI + UV + Uvicorn
├── docs/         # PRD e documentação
└── scripts/      # Lab legado de exploração e-SAJ (não é o backend do produto)
```

## Pré-requisitos

- [Bun](https://bun.sh/) (frontend)
- Python 3.12+ e [UV](https://docs.astral.sh/uv/) (backend)
- (Opcional) Docker — para build da imagem do backend

### UV no Windows / Git Bash

Se `uv` não for reconhecido (`command not found`), use via Python:

```bash
python -m pip install uv   # uma vez
python -m uv --version
```

Os comandos abaixo usam `python -m uv`. Se o UV estiver no PATH, pode trocar por só `uv`.

## Frontend

```bash
cd frontend
cp .env.example .env   # VITE_API_URL=http://localhost:8000
bun install
bun run dev            # http://localhost:3000
```

Build de produção:

```bash
cd frontend
bun run build
```

## Backend

```bash
cd backend
cp .env.example .env
python -m uv sync
python -m uv run playwright install chromium   # binário do browser (só na 1ª vez)
python -m uv run uvicorn app.main:app --reload --port 8000
```

> Sem o `playwright install chromium`, a validação de credenciais do e-SAJ falha com “portal indisponível” — o Chromium headless não está no PATH até esse comando baixar o binário.

> Os jobs do APScheduler (pipes a cada 10 min, renovação de cookie às 1h em Brasília) **não** rodam com `APP_ENV=development`. Para ligá-los localmente, defina `SCHEDULER_ENABLED=true` no `.env`. Em produção (`APP_ENV=production`) eles ligam sozinhos.

Health check: [http://localhost:8000/health](http://localhost:8000/health) → `{ "status": "ok" }`

Docs interativas (dev): [http://localhost:8000/docs](http://localhost:8000/docs)

Se a porta 8000 estiver ocupada (`WinError 10013`), use outra:

```bash
python -m uv run uvicorn app.main:app --reload --port 8001
```

(e ajuste `VITE_API_URL` no frontend se necessário)

## Banco de Dados

PostgreSQL hospedado no [Railway](https://railway.app/), com SQLAlchemy 2.0 (async/asyncpg) e migrations via Alembic.

### Connection string

No projeto do Railway, abra o serviço Postgres → aba **Variables** → copie `DATABASE_PUBLIC_URL` (a `DATABASE_URL` interna só funciona entre serviços dentro do Railway) e cole em `backend/.env`:

```
DATABASE_URL=postgresql://postgres:senha@monorail.proxy.rlwy.net:20000/railway
```

Não precisa ajustar o driver: `app/core/config.py` converte `postgresql://` para `postgresql+asyncpg://` e remove `sslmode`, que o asyncpg não aceita.

### Migrations

```bash
cd backend
python -m uv run alembic upgrade head      # aplica todas as migrations
python -m uv run alembic current           # revisão aplicada no banco
python -m uv run alembic downgrade -1      # desfaz a última
```

Depois de mudar qualquer model em `app/models/`:

```bash
python -m uv run alembic revision --autogenerate -m "descrição da mudança"
```

Revise o arquivo gerado em `app/db/migrations/versions/` antes de aplicar. Para inspecionar o SQL sem tocar no banco: `python -m uv run alembic upgrade head --sql`.

### Verificar a conexão

Com o servidor rodando: [http://localhost:8000/health/db](http://localhost:8000/health/db) → `{ "status": "ok", "database": "connected" }`

### Docker (backend)

```bash
cd backend
docker build -t automacao-backend .
docker run --rm -p 8000:8000 automacao-backend
```

O `CMD` respeita `PORT` (Railway injeta; local o default é 8000). A imagem baixa o Chromium do Playwright no build.

### Deploy da API no Railway

O Postgres do projeto já está no Railway. Para o serviço da **API**: Root Directory `backend`, variáveis como em `backend/.env.production.example` (nomes, sem colar o `.env` local). Passo a passo: [docs/modulos/deploy.md](docs/modulos/deploy.md).

## Lab legado (`scripts/esaj`)

Pasta de exploração (login Playwright, cookies, parsers cpopg). **Não** faz parte do backend de produto; o código útil será portado para `backend/app/services/` nas próximas etapas.

## Documentação

- [docs/PRD.md](docs/PRD.md) — produto, stack e arquitetura
