"""Regras dos arquivos do Drive e da conexão com o Google (ADR-022).

Toda consulta filtra `user_id` no banco. Pasta ou arquivo de outra pessoa
responde 404. O byte nunca passa pelo Postgres: o backend o repassa ao Google
com o token da pessoa, e a ficha guarda só nome, tipo, tamanho e origem.
"""

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.arquivos_drive import (
    ArquivoInvalidoError,
    sanitizar_nome,
    validar_envio,
    validar_metadados_google,
)
from app.core.security import encrypt_secret
from app.models.drive_arquivo import (
    ORIGEM_DRIVE,
    ORIGEM_ELABORACAO,
    ORIGEM_UPLOAD,
    DriveArquivo,
)
from app.models.drive_conexao import DriveConexao
from app.schemas.drive import ArquivoSchema, DriveStatusSchema
from app.services import oauth_google_drive
from app.services.drive import pasta_do_usuario
from app.services.drive_google import (
    ClienteDrive,
    DriveDesconectadoError,
    DriveGoogleError,
    DriveRecursoAusenteError,
    url_do_arquivo,
)

logger = logging.getLogger(__name__)

ORIGENS_ENVIO = frozenset({ORIGEM_UPLOAD, ORIGEM_ELABORACAO})

_NAO_ENCONTRADO = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Arquivo não encontrado",
)
_DESCONECTADO = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Conecte o Google Drive para continuar",
)
_FALHA_GOOGLE = HTTPException(
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="O Google Drive não respondeu como esperado. Tente de novo em instantes",
)


def _ficha(arquivo: DriveArquivo) -> ArquivoSchema:
    return ArquivoSchema(
        id=arquivo.id,
        pasta_id=arquivo.pasta_id,
        nome=arquivo.nome,
        mime_type=arquivo.mime_type,
        tamanho=arquivo.tamanho,
        origem=arquivo.origem,
        ausente_no_google=arquivo.ausente_no_google,
        url_drive=url_do_arquivo(arquivo.google_file_id),
        created_at=arquivo.created_at,
    )


async def conexao_do_usuario(db: AsyncSession, user_id: UUID) -> DriveConexao | None:
    return await db.scalar(select(DriveConexao).where(DriveConexao.user_id == user_id))


async def _cliente(db: AsyncSession, user_id: UUID) -> ClienteDrive:
    conexao = await conexao_do_usuario(db, user_id)
    if conexao is None:
        raise _DESCONECTADO
    return ClienteDrive(db, conexao)


async def _arquivo_do_usuario(db: AsyncSession, user_id: UUID, arquivo_id: UUID) -> DriveArquivo:
    arquivo = await db.scalar(
        select(DriveArquivo).where(DriveArquivo.id == arquivo_id, DriveArquivo.user_id == user_id)
    )
    if arquivo is None:
        raise _NAO_ENCONTRADO
    return arquivo


def _tocar(pasta) -> None:
    pasta.updated_at = datetime.now(UTC)


# --- conexão ----------------------------------------------------------------


async def status_conexao(db: AsyncSession, user_id: UUID) -> DriveStatusSchema:
    return DriveStatusSchema(
        configurado=oauth_google_drive.configurado(),
        picker_configurado=oauth_google_drive.picker_configurado(),
        conectado=await conexao_do_usuario(db, user_id) is not None,
    )


async def salvar_conexao(db: AsyncSession, user_id: UUID, tokens: dict) -> None:
    """Grava ou troca o token. O refresh anterior é preservado se o Google não mandar outro."""
    conexao = await conexao_do_usuario(db, user_id)
    anterior = ClienteDrive(db, conexao).payload_atual() if conexao is not None else None
    payload = oauth_google_drive.montar_payload(tokens, anterior=anterior)
    if not payload.get("refresh_token"):
        raise DriveDesconectadoError("SemRefreshToken")
    cifrado = encrypt_secret(json.dumps(payload))
    if conexao is None:
        db.add(DriveConexao(user_id=user_id, token_encrypted=cifrado))
    else:
        conexao.token_encrypted = cifrado
    await db.commit()


async def desconectar(db: AsyncSession, user_id: UUID) -> DriveStatusSchema:
    conexao = await conexao_do_usuario(db, user_id)
    if conexao is not None:
        await ClienteDrive(db, conexao).revogar()
        await db.delete(conexao)
        await db.commit()
    return await status_conexao(db, user_id)


async def token_do_picker(db: AsyncSession, user_id: UUID) -> tuple[str, int]:
    cliente = await _cliente(db, user_id)
    try:
        return await cliente.token_para_picker()
    except DriveDesconectadoError as exc:
        raise _DESCONECTADO from exc
    except DriveGoogleError as exc:
        raise _FALHA_GOOGLE from exc


# --- arquivos ---------------------------------------------------------------


async def listar(db: AsyncSession, user_id: UUID, pasta_id: UUID) -> list[ArquivoSchema]:
    await pasta_do_usuario(db, user_id, pasta_id)
    arquivos = (
        await db.scalars(
            select(DriveArquivo)
            .where(DriveArquivo.pasta_id == pasta_id, DriveArquivo.user_id == user_id)
            .order_by(DriveArquivo.created_at.desc())
        )
    ).all()
    return [_ficha(item) for item in arquivos]


def _recusa(exc: ArquivoInvalidoError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


async def enviar(
    db: AsyncSession,
    user_id: UUID,
    pasta_id: UUID,
    *,
    nome: str | None,
    conteudo: bytes,
    origem: str,
) -> ArquivoSchema:
    if origem not in ORIGENS_ENVIO:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Origem inválida")
    pasta = await pasta_do_usuario(db, user_id, pasta_id)
    try:
        nome_limpo, mime = validar_envio(nome, conteudo)
    except ArquivoInvalidoError as exc:
        raise _recusa(exc) from exc

    cliente = await _cliente(db, user_id)
    try:
        pasta_google = await cliente.garantir_pasta(pasta)
        enviado = await cliente.enviar(nome_limpo, mime, conteudo, pasta_google)
    except DriveDesconectadoError as exc:
        raise _DESCONECTADO from exc
    except DriveGoogleError as exc:
        raise _FALHA_GOOGLE from exc

    arquivo = DriveArquivo(
        user_id=user_id,
        pasta_id=pasta.id,
        google_file_id=str(enviado["id"]),
        nome=nome_limpo,
        mime_type=mime,
        tamanho=len(conteudo),
        origem=origem,
    )
    db.add(arquivo)
    _tocar(pasta)
    await db.commit()
    await db.refresh(arquivo)
    return _ficha(arquivo)


async def vincular(
    db: AsyncSession, user_id: UUID, pasta_id: UUID, google_file_id: str
) -> ArquivoSchema:
    """Arquivo escolhido no seletor do Google. Só a ficha é gravada."""
    pasta = await pasta_do_usuario(db, user_id, pasta_id)
    cliente = await _cliente(db, user_id)
    try:
        dados = await cliente.metadados(google_file_id)
    except DriveRecursoAusenteError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O Google Drive não liberou este arquivo. Escolha-o de novo no seletor",
        ) from exc
    except DriveDesconectadoError as exc:
        raise _DESCONECTADO from exc
    except DriveGoogleError as exc:
        raise _FALHA_GOOGLE from exc

    if dados.get("trashed"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O arquivo está na lixeira do Google Drive",
        )
    mime = dados.get("mimeType")
    tamanho_bruto = dados.get("size")
    tamanho = int(tamanho_bruto) if isinstance(tamanho_bruto, str) and tamanho_bruto.isdigit() else None
    try:
        validar_metadados_google(mime, tamanho)
        nome = sanitizar_nome(dados.get("name"))
    except ArquivoInvalidoError as exc:
        raise _recusa(exc) from exc

    arquivo = DriveArquivo(
        user_id=user_id,
        pasta_id=pasta.id,
        google_file_id=google_file_id,
        nome=nome,
        mime_type=str(mime),
        tamanho=tamanho,
        origem=ORIGEM_DRIVE,
    )
    db.add(arquivo)
    _tocar(pasta)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este arquivo já está nesta pasta",
        ) from exc
    await db.refresh(arquivo)
    return _ficha(arquivo)


async def baixar(db: AsyncSession, user_id: UUID, arquivo_id: UUID) -> tuple[str, str, bytes]:
    arquivo = await _arquivo_do_usuario(db, user_id, arquivo_id)
    cliente = await _cliente(db, user_id)
    try:
        conteudo = await cliente.baixar(arquivo.google_file_id)
    except DriveRecursoAusenteError as exc:
        arquivo.ausente_no_google = True
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O arquivo não está mais no Google Drive",
        ) from exc
    except DriveDesconectadoError as exc:
        raise _DESCONECTADO from exc
    except DriveGoogleError as exc:
        raise _FALHA_GOOGLE from exc
    return arquivo.nome, arquivo.mime_type, conteudo


async def mover(
    db: AsyncSession, user_id: UUID, arquivo_id: UUID, destino_id: UUID
) -> ArquivoSchema:
    arquivo = await _arquivo_do_usuario(db, user_id, arquivo_id)
    destino = await pasta_do_usuario(db, user_id, destino_id)
    if arquivo.pasta_id == destino.id:
        return _ficha(arquivo)

    repetido = await db.scalar(
        select(DriveArquivo.id).where(
            DriveArquivo.pasta_id == destino.id,
            DriveArquivo.google_file_id == arquivo.google_file_id,
        )
    )
    if repetido is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este arquivo já está nessa pasta",
        )

    origem_pasta = await pasta_do_usuario(db, user_id, arquivo.pasta_id)
    # Arquivo escolhido no seletor é da pessoa: a organização do Drive dela não é tocada.
    if arquivo.origem != ORIGEM_DRIVE:
        cliente = await _cliente(db, user_id)
        try:
            pasta_google = await cliente.garantir_pasta(destino)
            await cliente.mover(arquivo.google_file_id, pasta_google, origem_pasta.google_folder_id)
        except DriveRecursoAusenteError as exc:
            arquivo.ausente_no_google = True
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O arquivo não está mais no Google Drive",
            ) from exc
        except DriveDesconectadoError as exc:
            raise _DESCONECTADO from exc
        except DriveGoogleError as exc:
            raise _FALHA_GOOGLE from exc

    arquivo.pasta_id = destino.id
    _tocar(destino)
    _tocar(origem_pasta)
    await db.commit()
    await db.refresh(arquivo)
    return _ficha(arquivo)


async def excluir(db: AsyncSession, user_id: UUID, arquivo_id: UUID) -> None:
    """Upload vai para a lixeira do Drive. Arquivo do seletor só perde a ficha."""
    arquivo = await _arquivo_do_usuario(db, user_id, arquivo_id)
    if arquivo.origem != ORIGEM_DRIVE:
        conexao = await conexao_do_usuario(db, user_id)
        # Sem conexão não há como falar com o Google: a ficha sai e o arquivo fica no Drive.
        if conexao is not None:
            try:
                await ClienteDrive(db, conexao).lixeira(arquivo.google_file_id)
            except DriveDesconectadoError:
                pass
            except DriveGoogleError as exc:
                raise _FALHA_GOOGLE from exc
    pasta = await pasta_do_usuario(db, user_id, arquivo.pasta_id)
    await db.delete(arquivo)
    _tocar(pasta)
    await db.commit()
