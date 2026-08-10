"""Dependencies compartilhadas da API."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenInvalidoError, decode_access_token
from app.db.session import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

_CREDENCIAIS_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Resolve o usuário a partir do access token — única fonte de `user_id`.

    Nenhuma rota deve aceitar `user_id` vindo do cliente.
    """
    if credentials is None:
        raise _CREDENCIAIS_INVALIDAS

    try:
        user_id = decode_access_token(credentials.credentials)
    except TokenInvalidoError as exc:
        raise _CREDENCIAIS_INVALIDAS from exc

    user = await db.get(User, user_id)
    if user is None:
        # Token válido mas conta removida: mesma resposta genérica.
        raise _CREDENCIAIS_INVALIDAS

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
