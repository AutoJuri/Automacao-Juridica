"""Entrypoint FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import auth, credentials, notifications, processos
from app.core.config import get_settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.scheduler import iniciar_scheduler, parar_scheduler
from app.core.security_headers import SecurityHeadersMiddleware
from app.db.session import get_db

settings = get_settings()

# Métodos e headers que a SPA realmente usa (axios + cookie de refresh).
# Nunca `*` — reduz a superfície do preflight CORS.
CORS_ALLOW_METHODS = ["GET", "POST", "PATCH", "DELETE", "HEAD"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type", "Accept"]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.scheduler_enabled:
        iniciar_scheduler()
    try:
        yield
    finally:
        if settings.scheduler_enabled:
            parar_scheduler()


app = FastAPI(
    title="Automação Jurídica API",
    description="Backend do MVP — autenticação, credenciais, painel de processos e notificações",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Por último = mais externo: os headers saem em toda resposta, inclusive no
# preflight OPTIONS do CORS. HSTS só fora de development (localhost é HTTP).
app.add_middleware(
    SecurityHeadersMiddleware,
    hsts=not settings.is_development,
)

app.include_router(auth.router)
app.include_router(credentials.router)
app.include_router(processos.router)
app.include_router(processos.router_intimacoes)
app.include_router(processos.router_audiencias)
app.include_router(notifications.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
