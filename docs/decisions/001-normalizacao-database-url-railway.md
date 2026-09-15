# ADR-001: Normalização da DATABASE_URL do Railway para asyncpg

**Data:** 2026-08-05
**Status:** Aceito

---

## Contexto

O Railway entrega a connection string no formato `postgresql://usuario:senha@host:porta/banco` (e às vezes com `?sslmode=require`). O SQLAlchemy async exige o driver `postgresql+asyncpg://`, e o `asyncpg` não aceita o parâmetro `sslmode` (ele é específico do psycopg2). Exigir que o desenvolvedor edite a URL manualmente a cada cópia aumenta o risco de erro e de documentação desatualizada.

## Decisão

Centralizar a conversão em `Settings.sqlalchemy_url` (`backend/app/core/config.py`):

1. Se o driver for `postgres` ou `postgresql`, trocar para `postgresql+asyncpg`
2. Remover `sslmode` da query string
3. Aceitar no `.env` a URL exatamente como vem do Railway (`DATABASE_PUBLIC_URL` em desenvolvimento local)

Engine, Alembic (`env.py`) e qualquer código futuro devem usar `settings.sqlalchemy_url`, nunca `settings.database_url` cru.

## Alternativas consideradas

- **Documentar e exigir que o usuário edite a URL no `.env`:** descartado — frágil, fácil esquecer `sslmode` e gerar falha opaca de conexão.
- **Usar psycopg (sync) ou psycopg3 com dialect async:** descartado — o PRD define SQLAlchemy 2.0 async + asyncpg; manter o stack alinhado.

## Consequências

- Colar a URL do Railway no `.env` funciona sem ajuste manual.
- Em produção, dentro do Railway, a variável interna `DATABASE_URL` também é aceita (mesmo prefixo `postgresql://`).
- Quem adicionar um novo ponto de conexão precisa lembrar de usar `sqlalchemy_url`, não a string crua.
