"""Pastas do Drive do usuário.

Toda leitura e escrita filtra `user_id` no banco. Pasta ou processo de outra
pessoa responde 404. `total_arquivos` conta as fichas de `drive_arquivos`; o
byte de cada arquivo mora no Google Drive da pessoa (ADR-022). Apagar a pasta
aqui nunca mexe no Google.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.drive_arquivo import DriveArquivo
from app.models.drive_pasta import DrivePasta
from app.models.processo import Processo
from app.schemas.drive import (
    PastaCreateSchema,
    PastaProcessoSchema,
    PastaSchema,
    PastaUpdateSchema,
)

LIMITE_PASTAS = 200

_NAO_ENCONTRADA = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Pasta não encontrada",
)
_PROCESSO_NAO_ENCONTRADO = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Processo não encontrado",
)


def _nome_parte(parte: dict | None) -> str | None:
    if not parte:
        return None
    nome = parte.get("nome") or parte.get("nomeSocial")
    if isinstance(nome, str) and nome.strip():
        return nome.strip()
    return None


def _pasta(pasta: DrivePasta, total_arquivos: int = 0) -> PastaSchema:
    processo = pasta.processo
    return PastaSchema(
        id=pasta.id,
        nome=pasta.nome,
        processo=(
            PastaProcessoSchema(
                id=processo.id,
                nu_processo=processo.nu_processo,
                autor=_nome_parte(processo.parte_ativa),
                reu=_nome_parte(processo.parte_passiva),
            )
            if processo is not None
            else None
        ),
        total_arquivos=total_arquivos,
        updated_at=pasta.updated_at,
    )


async def _por_id(db: AsyncSession, user_id: UUID, pasta_id: UUID) -> DrivePasta:
    pasta = await db.scalar(
        select(DrivePasta)
        .where(DrivePasta.id == pasta_id, DrivePasta.user_id == user_id)
        .options(selectinload(DrivePasta.processo))
        # Relê o vínculo depois de trocar ou soltar o `processo_id`.
        .execution_options(populate_existing=True)
    )
    if pasta is None:
        raise _NAO_ENCONTRADA
    return pasta


async def pasta_do_usuario(db: AsyncSession, user_id: UUID, pasta_id: UUID) -> DrivePasta:
    """Pasta do usuário ou 404. Também usada pelos arquivos."""
    return await _por_id(db, user_id, pasta_id)


async def _totais(db: AsyncSession, user_id: UUID, ids: list[UUID]) -> dict[UUID, int]:
    if not ids:
        return {}
    linhas = await db.execute(
        select(DriveArquivo.pasta_id, func.count(DriveArquivo.id))
        .where(DriveArquivo.user_id == user_id, DriveArquivo.pasta_id.in_(ids))
        .group_by(DriveArquivo.pasta_id)
    )
    return {pasta_id: total for pasta_id, total in linhas.all()}


async def _schema(db: AsyncSession, user_id: UUID, pasta: DrivePasta) -> PastaSchema:
    totais = await _totais(db, user_id, [pasta.id])
    return _pasta(pasta, totais.get(pasta.id, 0))


async def _processo_do_usuario(db: AsyncSession, user_id: UUID, processo_id: UUID) -> None:
    existe = await db.scalar(
        select(Processo.id).where(Processo.id == processo_id, Processo.user_id == user_id)
    )
    if existe is None:
        raise _PROCESSO_NAO_ENCONTRADO


async def listar(db: AsyncSession, user_id: UUID) -> list[PastaSchema]:
    pastas = list(
        (
            await db.scalars(
                select(DrivePasta)
                .where(DrivePasta.user_id == user_id)
                .options(selectinload(DrivePasta.processo))
                .order_by(DrivePasta.updated_at.desc())
                .limit(LIMITE_PASTAS)
            )
        ).all()
    )
    totais = await _totais(db, user_id, [item.id for item in pastas])
    return [_pasta(item, totais.get(item.id, 0)) for item in pastas]


async def obter(db: AsyncSession, user_id: UUID, pasta_id: UUID) -> PastaSchema:
    return await _schema(db, user_id, await _por_id(db, user_id, pasta_id))


async def criar(db: AsyncSession, user_id: UUID, dados: PastaCreateSchema) -> PastaSchema:
    if dados.processo_id is not None:
        await _processo_do_usuario(db, user_id, dados.processo_id)
    pasta = DrivePasta(user_id=user_id, nome=dados.nome, processo_id=dados.processo_id)
    db.add(pasta)
    await db.commit()
    return await _schema(db, user_id, await _por_id(db, user_id, pasta.id))


async def atualizar(
    db: AsyncSession, user_id: UUID, pasta_id: UUID, dados: PastaUpdateSchema
) -> PastaSchema:
    pasta = await _por_id(db, user_id, pasta_id)
    if dados.nome is not None:
        pasta.nome = dados.nome
    if "processo_id" in dados.model_fields_set:
        if dados.processo_id is not None:
            await _processo_do_usuario(db, user_id, dados.processo_id)
        pasta.processo_id = dados.processo_id
    pasta.updated_at = datetime.now(UTC)
    await db.commit()
    return await _schema(db, user_id, await _por_id(db, user_id, pasta_id))


async def excluir(db: AsyncSession, user_id: UUID, pasta_id: UUID) -> None:
    """Apaga a pasta e as fichas. Nada é apagado no Google Drive."""
    pasta = await _por_id(db, user_id, pasta_id)
    await db.delete(pasta)
    await db.commit()
