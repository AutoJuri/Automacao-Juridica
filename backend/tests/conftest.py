"""Fixtures compartilhadas.

A suíte unitária (painel, pipes, etc.) continua sem banco. A fixture
`cliente_auth` é só para integração de `/auth/*`: uma transação por teste,
`commit` da rota vira savepoint, e o rollback no fim não deixa usuário no
Postgres (mesmo Railway de desenvolvimento).

Engine próprio (NullPool) — o `engine` global de `app.db.session` vive no
loop do processo e quebra no teardown do pytest-asyncio (loop por teste).
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture
async def cliente_auth():
    """Cliente HTTP + sessão SQL na mesma transação do teste."""
    limiter_antes = getattr(limiter, "enabled", True)
    limiter.enabled = False
    engine = create_async_engine(
        get_settings().sqlalchemy_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as conexao:
            transacao = await conexao.begin()
            sessao = AsyncSession(
                bind=conexao,
                expire_on_commit=False,
                autoflush=False,
                join_transaction_mode="create_savepoint",
            )

            async def _get_db_teste():
                yield sessao

            app.dependency_overrides[get_db] = _get_db_teste
            try:
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    yield client, sessao
            finally:
                app.dependency_overrides.pop(get_db, None)
                await sessao.close()
                if transacao.is_active:
                    await transacao.rollback()
    finally:
        await engine.dispose()
        limiter.enabled = limiter_antes
