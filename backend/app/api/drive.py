"""Rotas das pastas e dos arquivos do Drive.

`user_id` vem do JWT. Pasta, arquivo ou processo de outra pessoa responde 404.
O byte do arquivo mora no Google Drive da pessoa (ADR-022).
"""

from typing import Annotated, Literal
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, Request, Response, UploadFile, status

from app.api.deps import CurrentUser, DbSession
from app.core.arquivos_drive import TAMANHO_MAX
from app.core.rate_limit import LIMITE_DRIVE_ENVIO, limiter
from app.schemas.drive import (
    ArquivoSchema,
    MoverArquivoSchema,
    PastaCreateSchema,
    PastaSchema,
    PastaUpdateSchema,
    VincularArquivoSchema,
)
from app.services import drive as servico
from app.services import drive_arquivos as arquivos

router = APIRouter(prefix="/drive", tags=["drive"])

# Folga para o corpo multipart (cabeçalhos das partes) acima do teto do arquivo.
_FOLGA_MULTIPART = 1024 * 1024
_LEITURA_EM_BLOCOS = 1024 * 1024


@router.get("/pastas", response_model=list[PastaSchema])
async def listar(current_user: CurrentUser, db: DbSession) -> list[PastaSchema]:
    return await servico.listar(db, current_user.id)


@router.post("/pastas", response_model=PastaSchema, status_code=status.HTTP_201_CREATED)
async def criar(
    dados: PastaCreateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> PastaSchema:
    return await servico.criar(db, current_user.id, dados)


@router.get("/pastas/{pasta_id}", response_model=PastaSchema)
async def obter(pasta_id: UUID, current_user: CurrentUser, db: DbSession) -> PastaSchema:
    return await servico.obter(db, current_user.id, pasta_id)


@router.patch("/pastas/{pasta_id}", response_model=PastaSchema)
async def atualizar(
    pasta_id: UUID,
    dados: PastaUpdateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> PastaSchema:
    return await servico.atualizar(db, current_user.id, pasta_id, dados)


@router.delete("/pastas/{pasta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir(pasta_id: UUID, current_user: CurrentUser, db: DbSession) -> None:
    await servico.excluir(db, current_user.id, pasta_id)


# --- arquivos -----------------------------------------------------------------


@router.get("/pastas/{pasta_id}/arquivos", response_model=list[ArquivoSchema])
async def listar_arquivos(
    pasta_id: UUID, current_user: CurrentUser, db: DbSession
) -> list[ArquivoSchema]:
    return await arquivos.listar(db, current_user.id, pasta_id)


async def _ler_limitado(arquivo: UploadFile) -> bytes:
    partes: list[bytes] = []
    total = 0
    while bloco := await arquivo.read(_LEITURA_EM_BLOCOS):
        total += len(bloco)
        if total > TAMANHO_MAX:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="O arquivo passa de 25 MB",
            )
        partes.append(bloco)
    return b"".join(partes)


@router.post(
    "/pastas/{pasta_id}/arquivos",
    response_model=ArquivoSchema,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(LIMITE_DRIVE_ENVIO)
async def enviar_arquivo(
    request: Request,
    pasta_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    arquivo: Annotated[UploadFile, File()],
    origem: Annotated[Literal["upload", "elaboracao"], Form()] = "upload",
) -> ArquivoSchema:
    declarado = request.headers.get("content-length")
    if declarado and declarado.isdigit() and int(declarado) > TAMANHO_MAX + _FOLGA_MULTIPART:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="O arquivo passa de 25 MB",
        )
    conteudo = await _ler_limitado(arquivo)
    return await arquivos.enviar(
        db,
        current_user.id,
        pasta_id,
        nome=arquivo.filename,
        conteudo=conteudo,
        origem=origem,
    )


@router.post(
    "/pastas/{pasta_id}/arquivos/vincular",
    response_model=ArquivoSchema,
    status_code=status.HTTP_201_CREATED,
)
async def vincular_arquivo(
    pasta_id: UUID,
    dados: VincularArquivoSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ArquivoSchema:
    return await arquivos.vincular(db, current_user.id, pasta_id, dados.google_file_id)


@router.get("/arquivos/{arquivo_id}/conteudo")
async def baixar_arquivo(arquivo_id: UUID, current_user: CurrentUser, db: DbSession) -> Response:
    nome, mime, conteudo = await arquivos.baixar(db, current_user.id, arquivo_id)
    return Response(
        content=conteudo,
        media_type=mime,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(nome, safe='')}",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.patch("/arquivos/{arquivo_id}", response_model=ArquivoSchema)
async def mover_arquivo(
    arquivo_id: UUID,
    dados: MoverArquivoSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ArquivoSchema:
    return await arquivos.mover(db, current_user.id, arquivo_id, dados.pasta_id)


@router.delete("/arquivos/{arquivo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_arquivo(arquivo_id: UUID, current_user: CurrentUser, db: DbSession) -> None:
    await arquivos.excluir(db, current_user.id, arquivo_id)
