"""PDF de uma movimentação, para o advogado ver dentro da plataforma (ADR-027).

O cookie do e-SAJ é descriptografado só aqui, num cliente httpx novo, e
descartado. O PDF fica em memória até a resposta sair: não é gravado, não
entra em log e só vai para o dono do processo. Query da URL não é logada.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import DecriptografiaError, decrypt_secret
from app.models.movimentacao import Movimentacao
from app.models.processo import Processo
from app.models.tribunal import (
    SESSION_STATUS_ATIVO,
    TRIBUNAL_ESAJ_TJSP,
    TribunalSession,
)
from app.services.esaj_cpo_parser import cd_documento_da_url, url_cpo_publica, url_documento_publica
from app.services.esaj_documentos import (
    EsajDocumentoGrandeError,
    EsajDocumentoNaoPdfError,
    baixar_documento,
)
from app.services.esaj_http import (
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
    montar_client,
)
from app.services.pipes.pipe_movimentacoes import localizar_url_documento

logger = logging.getLogger(__name__)


class DocumentoNaoEncontradoError(Exception):
    """Movimentação inexistente, de outro usuário ou sem URL de documento."""


class SessaoEsajIndisponivelError(Exception):
    """Sem sessão ativa com cookie válido, ou o portal pediu login de novo."""


class PortalLimitandoError(Exception):
    """O e-SAJ respondeu 429 nesta abertura. A sessão de coleta não muda."""


class DocumentoSemPdfError(Exception):
    """O portal respondeu, mas não entregou um PDF (ou passou do teto)."""


class PortalForaDoArError(Exception):
    """Timeout ou erro de rede com o portal. Vale tentar de novo depois."""


async def _url_do_documento(
    db: AsyncSession, user_id: UUID, processo_id: UUID, movimentacao_id: UUID
) -> tuple[str, str]:
    linha = (
        await db.execute(
            select(Movimentacao.url_documento, Processo.url_cpo)
            .join(Processo, Movimentacao.processo_id == Processo.id)
            .where(
                Processo.id == processo_id,
                Processo.user_id == user_id,
                Movimentacao.id == movimentacao_id,
                Movimentacao.processo_id == processo_id,
            )
        )
    ).first()
    if linha is None:
        raise DocumentoNaoEncontradoError
    url, url_cpo = linha
    publica = url_documento_publica(url)
    ficha = url_cpo_publica(url_cpo)
    if publica is None or ficha is None:
        raise DocumentoNaoEncontradoError
    return publica, ficha


async def _sessao_ativa(db: AsyncSession, user_id: UUID) -> TribunalSession:
    sessao = await db.scalar(
        select(TribunalSession).where(
            TribunalSession.user_id == user_id,
            TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
        )
    )
    if (
        sessao is None
        or sessao.cookie_encrypted is None
        or sessao.cookie_expirado()
        or sessao.status != SESSION_STATUS_ATIVO
    ):
        raise SessaoEsajIndisponivelError
    return sessao


def _cookies_da_sessao(sessao: TribunalSession) -> dict | list:
    try:
        carregado = json.loads(decrypt_secret(sessao.cookie_encrypted or b""))
    except (DecriptografiaError, ValueError):
        raise SessaoEsajIndisponivelError from None
    if not isinstance(carregado, (dict, list)):
        raise SessaoEsajIndisponivelError
    return carregado


async def baixar_pdf_da_movimentacao(
    db: AsyncSession, user_id: UUID, processo_id: UUID, movimentacao_id: UUID
) -> bytes:
    """Bytes do PDF. Quem chama devolve e descarta, sem gravar."""
    url, url_cpo = await _url_do_documento(db, user_id, processo_id, movimentacao_id)
    cd_documento = cd_documento_da_url(url)
    if cd_documento is None:
        raise DocumentoNaoEncontradoError
    sessao = await _sessao_ativa(db, user_id)

    cookies: dict | list | None = None
    try:
        cookies = _cookies_da_sessao(sessao)
        async with montar_client(cookies) as client:
            viva = await localizar_url_documento(client, url_cpo, cd_documento)
            if viva is None:
                raise DocumentoSemPdfError
            return await baixar_documento(client, viva, referer=url_cpo)
    except EsajSessaoInvalidaError:
        raise SessaoEsajIndisponivelError from None
    except EsajRateLimitError:
        # Não marca a sessão `bloqueado`. Esse status para a coleta de 10
        # minutos. Aqui o 429 é só desta abertura.
        raise PortalLimitandoError from None
    except (EsajDocumentoNaoPdfError, EsajDocumentoGrandeError):
        raise DocumentoSemPdfError from None
    except EsajPortalIndisponivelError as exc:
        logger.info("Documento da movimentação indisponível (causa=%s)", type(exc).__name__)
        raise PortalForaDoArError from None
    finally:
        cookies = None
