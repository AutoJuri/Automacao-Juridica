"""PDF da movimentação (ADR-027). `user_id` vem do JWT. Processo alheio é 404.

O arquivo sai só para o dono, sem cache, e não é gravado. Nenhum cookie
do e-SAJ vai na resposta.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import LIMITE_DOCUMENTO_PDF, limiter
from app.services.documento_movimentacao import (
    DocumentoNaoEncontradoError,
    DocumentoSemPdfError,
    PortalForaDoArError,
    PortalLimitandoError,
    SessaoEsajIndisponivelError,
    baixar_pdf_da_movimentacao,
)

router = APIRouter(prefix="/processos", tags=["processos"])

_CABECALHOS_PDF = {
    "Content-Disposition": 'inline; filename="documento.pdf"',
    "Cache-Control": "no-store, private",
    "Pragma": "no-cache",
}


@router.get(
    "/{processo_id}/movimentacoes/{movimentacao_id}/documento",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
@limiter.limit(LIMITE_DOCUMENTO_PDF)
async def documento_da_movimentacao(
    request: Request,
    processo_id: UUID,
    movimentacao_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    try:
        pdf = await baixar_pdf_da_movimentacao(db, current_user.id, processo_id, movimentacao_id)
    except DocumentoNaoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado"
        ) from None
    except SessaoEsajIndisponivelError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sessão do e-SAJ indisponível. Reconecte em Configurações.",
        ) from None
    except PortalLimitandoError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="O e-SAJ está limitando os acessos. Tente novamente mais tarde.",
        ) from None
    except DocumentoSemPdfError:
        raise HTTPException(
            status_code=422,
            detail="O e-SAJ não entregou um PDF para este documento.",
        ) from None
    except PortalForaDoArError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="O e-SAJ não respondeu. Tente novamente.",
        ) from None
    return Response(content=pdf, media_type="application/pdf", headers=_CABECALHOS_PDF)
