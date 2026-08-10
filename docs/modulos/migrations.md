# Módulo: Migrations e Camada de Dados

> Última atualização: 2026-08-09
> Camada: Infra / Backend

---

## O que este módulo faz

Define o schema PostgreSQL do MVP (9 tabelas do PRD), a sessão async do SQLAlchemy e as migrations Alembic. É a fundação de dados da qual auth, credentials, pipes e o painel dependem — sem endpoints de negócio nesta etapa, só o banco, os models e o health check de conexão.

---

## Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/db/base.py` | `DeclarativeBase` + naming convention de índices/constraints |
| `backend/app/db/session.py` | Engine async, `SessionLocal`, dependency `get_db()` |
| `backend/app/db/migrations/env.py` | Ambiente Alembic em modo async (asyncpg) |
| `backend/app/db/migrations/versions/0b7c41e5d9a3_initial_schema.py` | Migration inicial — cria as 9 tabelas |
| `backend/app/models/` | Models SQLAlchemy 2.0 (`Mapped` / `mapped_column`) |
| `backend/app/models/mixins.py` | PK UUID + `created_at` / `updated_at` com `sort_order` |
| `backend/app/core/config.py` | `Settings.sqlalchemy_url` — normaliza URL do Railway |
| `backend/alembic.ini` | Config Alembic (`script_location = app/db/migrations`) |
| `backend/app/main.py` | `GET /health` e `GET /health/db` |

---

## Endpoints (se módulo de backend)

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/health` | Liveness do processo FastAPI | Não |
| GET | `/health/db` | `SELECT 1` via `get_db()` — valida conexão com o Postgres | Não |

> Endpoints de negócio (auth, processos, etc.) entram nas próximas etapas.
> `user_id` nunca é aceito via body ou query — sempre virá do JWT.

---

## Comandos Alembic

```bash
cd backend
python -m uv run alembic upgrade head      # aplica todas as migrations
python -m uv run alembic current           # revisão aplicada no banco
python -m uv run alembic downgrade -1      # desfaz a última
python -m uv run alembic revision --autogenerate -m "descrição"
python -m uv run alembic upgrade head --sql  # inspeciona SQL sem tocar no banco
```

Revisar sempre o arquivo gerado em `app/db/migrations/versions/` antes do `upgrade`.

---

## Padrões seguidos neste módulo

- **ORM:** SQLAlchemy 2.0 async (`create_async_engine` + `async_sessionmaker`) com driver `asyncpg`
- **Migrations:** Alembic em modo async (`async_engine_from_config` + `connection.run_sync`)
- **URL:** `DATABASE_URL` aceita o formato cru do Railway (`postgresql://`); `Settings.sqlalchemy_url` converte para `postgresql+asyncpg://` e remove `sslmode`
- **Pool:** `pool_pre_ping=True` e `pool_recycle=1800` — o proxy público do Railway derruba conexões ociosas
- **PK:** UUID (`uuid.uuid4`) em todas as tabelas — nunca sequencial
- **Timestamps:** `DateTime(timezone=True)` com `server_default=func.now()`; `onupdate=func.now()` onde há `updated_at`
- **Campos sensíveis:** `cpf_encrypted`, `senha_encrypted`, `cookie_encrypted`, `email_oauth_token_encrypted` como `LargeBinary` (BYTEA) — criptografia AES entra na Etapa 3
- **Estados (`status`, `tipo`, `email_provider`):** `String` + constantes Python — sem ENUM nativo do Postgres (ver ADR-002)
- **FKs:** `ondelete="CASCADE"` para filhos obrigatórios; `SET NULL` nos `processo_id` / `user_id` nullable
- **Constraints:**
  - `UniqueConstraint(user_id, cd_processo)` em `processos`
  - `UniqueConstraint(user_id, tribunal)` em `tribunal_credentials` e `tribunal_sessions` — um advogado tem no máximo uma credencial/sessão ativa por tribunal
  - `UniqueConstraint(user_id, id_esaj)` em `intimacoes` e `audiencias` — unicidade por advogado, não global, para não colidir se o e-SAJ reaproveitar `id_esaj` entre contas diferentes
  - `UniqueConstraint(processo_id, data_movimentacao, descricao_hash)` em `movimentacoes` — chave natural do diff do ETL, usando o hash em vez da coluna `Text` diretamente (ver `descricao_hash` abaixo)
- **Índices adicionais:** `ix_tribunal_sessions_status_proximo_retry` (composto `status` + `proximo_retry`) — usado pelo scheduler para filtrar sessões pendentes de retry
- **Hash de conteúdo:** `Movimentacao.descricao_hash` (SHA-256, `String(64)`) é preenchido automaticamente por um `@validates("descricao")` sempre que `descricao` é atribuída — nenhum código chamador precisa calcular o hash manualmente. Necessário porque um índice UNIQUE do Postgres não aceita entradas maiores que ~2.7 KB, e a coluna `descricao` (`Text`) pode ultrapassar esse limite
- **Naming convention:** nomes estáveis de PK/FK/UQ/IX no `Base.metadata` — evita nomes automáticos do Postgres nas migrations
- **Autogenerate:** `app/models/__init__.py` importa e reexporta todos os models para o `Base.metadata` ficar completo
- **Logging do engine:** `echo=False` fixo no `create_async_engine` — o SQLAlchemy loga os binds das queries, o que arriscaria expor `password_hash` e campos `*_encrypted` em texto claro
- **Docker:** o container roda como usuário não-root (`appuser`), nunca como root

---

## Modelo de dados relacionado

Tabelas (revisões `0b7c41e5d9a3` + `34c3ebb0c7e4` + `38d4177c211b`):

```
users
├── refresh_tokens          (auth — só hash SHA-256 do token)
├── password_reset_tokens   (auth — uso único, expiração curta)
├── tribunal_credentials
├── tribunal_sessions
├── processos
│   ├── movimentacoes
│   ├── intimacoes      (processo_id nullable)
│   ├── audiencias      (processo_id nullable)
│   └── notifications   (processo_id nullable)
├── intimacoes
├── audiencias
├── notifications
└── job_logs            (user_id nullable — logs de sistema)
```

Exemplo representativo (`processos`):

```python
class Processo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processos"
    __table_args__ = (UniqueConstraint("user_id", "cd_processo"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tribunal: Mapped[str] = mapped_column(String(50), nullable=False)
    cd_processo: Mapped[str] = mapped_column(String(100), nullable=False)
    parte_ativa: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    parte_passiva: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # ... demais campos do PRD seção 9
```

Arquivos de model por domínio:

| Arquivo | Tabelas |
|---|---|
| `user.py` | `users` |
| `refresh_token.py` | `refresh_tokens` |
| `password_reset_token.py` | `password_reset_tokens` |
| `tribunal.py` | `tribunal_credentials`, `tribunal_sessions` |
| `processo.py` | `processos` |
| `movimentacao.py` | `movimentacoes` |
| `intimacao.py` | `intimacoes` |
| `audiencia.py` | `audiencias` |
| `notification.py` | `notifications` |
| `job_log.py` | `job_logs` |

Constantes de domínio (valores válidos de `status`/`tipo`) ficam no próprio arquivo do model (`SESSION_STATUSES`, `NOTIFICATION_TIPOS`, `JOB_TIPOS`, etc.).

---

## Dependências de outros módulos

| Módulo | Por quê depende |
|---|---|
| — | Fundação; não depende de outros módulos de produto |

Módulos futuros que vão depender deste:

| Módulo | Uso |
|---|---|
| `auth` | `users`, `refresh_tokens`, `password_reset_tokens`, JWT/bcrypt |
| `credentials` | `tribunal_credentials` + AES-256 |
| `processos` / pipes / etl | `processos`, `movimentacoes`, `intimacoes`, `audiencias` |
| `notifications` | Tabela `notifications` |
| `scheduler` | `job_logs`, `tribunal_sessions` |

---

## O que NÃO fazer aqui

- ❌ Não colocar `sqlalchemy.url` hardcoded no `alembic.ini` — a URL vem do `.env` via `env.py`
- ❌ Não usar a `DATABASE_URL` interna do Railway no desenvolvimento local — use `DATABASE_PUBLIC_URL` (a interna só resolve entre serviços dentro da rede do Railway)
- ❌ Não colar `?sslmode=require` na URL esperando que o asyncpg aceite — `Settings.sqlalchemy_url` já remove esse parâmetro
- ❌ Não criar ENUM nativo do Postgres para `status`/`tipo` — use `String` + constantes Python (ADR-002)
- ❌ Não retornar model ORM em endpoints futuros — sempre `ResponseSchema` Pydantic
- ❌ Não logar ou expor campos `*_encrypted` — a descriptografia só acontece em memória, na Etapa 3+
- ❌ Não aplicar `alembic revision --autogenerate` em produção sem revisar o arquivo gerado
- ❌ Não filtrar ownership em Python após buscar todos os registros — `WHERE user_id = current_user.id` no banco (quando os endpoints existirem)
- ❌ Não commitar `backend/.env` — só o `.env.example` com placeholder

---

## Histórico de mudanças relevantes

| Data | O que mudou |
|---|---|
| 2026-08-05 | Implementação inicial (Etapa 2): models, sessão async, Alembic, migration `0b7c41e5d9a3` aplicada no Postgres do Railway, `GET /health/db` |
| 2026-08-05 | Ajustes pós code-review: `UniqueConstraint(user_id, id_esaj)` em `intimacoes`/`audiencias`, `UniqueConstraint(user_id, tribunal)` em `tribunal_credentials`/`tribunal_sessions`, índice composto `status`+`proximo_retry` em `tribunal_sessions`, coluna `descricao_hash` (SHA-256) em `movimentacoes` para evitar estourar o limite de tamanho do índice UNIQUE, migration `34c3ebb0c7e4` aplicada; `echo=False` no engine; Dockerfile passa a rodar como usuário não-root |
| 2026-08-09 | Etapa 3 (auth): tabelas `refresh_tokens` e `password_reset_tokens` — migration `38d4177c211b` |
