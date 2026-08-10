"""Rate limiting das rotas públicas de autenticação.

Armazenamento em memória do processo — suficiente enquanto rodamos uma única
instância no Railway. Ao escalar horizontalmente é obrigatório trocar por um
backend compartilhado (`storage_uri="redis://..."`), senão cada réplica passa a
contar tentativas isoladamente e o limite efetivo vira N vezes maior.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

LIMITE_CADASTRO = "5/hour"
LIMITE_LOGIN = "10/hour"
LIMITE_RECUPERAR_SENHA = "3/hour"


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """429 com mensagem genérica — não revela o limite configurado."""
    assert isinstance(exc, RateLimitExceeded)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Muitas tentativas. Tente novamente mais tarde."},
    )
