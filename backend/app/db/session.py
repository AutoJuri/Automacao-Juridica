"""Engine e sessão async do PostgreSQL."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.sqlalchemy_url,
    # Desligado por padrão: o SQLAlchemy loga os binds das queries, o que
    # arriscaria expor password_hash e bytes criptografados em texto claro.
    echo=False,
    # O Railway fica atrás de um proxy que derruba conexões ociosas.
    pool_pre_ping=True,
    pool_recycle=1800,
    # Sem isso, uma conexão que o proxy segura sem responder prende o job
    # de 10 min para sempre (`max_instances=1` passa a pular os ciclos).
    connect_args={"timeout": 20, "command_timeout": 60},
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI: uma sessão por request."""
    async with SessionLocal() as session:
        yield session
