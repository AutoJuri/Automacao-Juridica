"""Leitura dos autos. `user_id` vem do JWT. Processo de outro advogado é 404."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import LIMITE_DOSSIE_LER, LIMITE_DOSSIE_ROTEIRO, limiter
from app.schemas.dossie import DossiePublicSchema, RoteiroSchema
from app.services.dossie import (
    LeituraEmAndamentoError,
    LimiteLeituraError,
    iniciar_leitura,
    obter_dossie,
    salvar_roteiro,
)

router = APIRouter(prefix="/processos", tags=["processos"])

_NAO_ENCONTRADO = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado"
)


@router.get("/{processo_id}/dossie", response_model=DossiePublicSchema)
async def consultar_dossie(
    processo_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DossiePublicSchema:
    dossie = await obter_dossie(db, current_user.id, processo_id)
    if dossie is None:
        raise _NAO_ENCONTRADO
    return dossie


@router.post("/{processo_id}/dossie/ler", response_model=DossiePublicSchema)
@limiter.limit(LIMITE_DOSSIE_LER)
async def ler_autos(
    request: Request,
    processo_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DossiePublicSchema:
    try:
        dossie = await iniciar_leitura(db, current_user.id, processo_id)
    except LeituraEmAndamentoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma leitura em andamento.",
        ) from None
    except LimiteLeituraError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas. Tente novamente mais tarde.",
        ) from None
    if dossie is None:
        raise _NAO_ENCONTRADO
    return dossie


@router.put("/{processo_id}/dossie/roteiro", response_model=DossiePublicSchema)
@limiter.limit(LIMITE_DOSSIE_ROTEIRO)
async def gravar_roteiro(
    request: Request,
    processo_id: UUID,
    body: RoteiroSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> DossiePublicSchema:
    dossie = await salvar_roteiro(db, current_user.id, processo_id, body)
    if dossie is None:
        raise _NAO_ENCONTRADO
    return dossie
