"""Leitura dos autos sob demanda (ADR-024).

O cookie do e-SAJ é descriptografado dentro da tarefa, usado e descartado.
Uma leitura por processo e por usuário. O PDF não é persistido.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from uuid import UUID, uuid5, NAMESPACE_URL

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.backoff import calcular_proximo_retry
from app.core.security import DecriptografiaError, decrypt_secret, encrypt_secret
from app.db.session import SessionLocal
from app.models.movimentacao import Movimentacao
from app.models.processo import Processo
from app.models.processo_documento import (
    STATUS_DOC_LIDO,
    STATUS_DOC_PARCIAL,
    STATUS_DOC_PENDENTE,
    STATUS_DOC_TERMINAIS,
    STATUS_DOSSIE_BLOQUEADO,
    STATUS_DOSSIE_ERRO,
    STATUS_DOSSIE_LENDO,
    STATUS_DOSSIE_LIMITE,
    STATUS_DOSSIE_OCIOSO,
    STATUS_DOSSIE_PRONTO,
    STATUS_DOSSIE_SEM,
    STATUS_DOSSIE_SESSAO,
    ProcessoDossie,
)
from app.models.tribunal import (
    SESSION_STATUS_ATIVO,
    SESSION_STATUS_BLOQUEADO,
    TRIBUNAL_ESAJ_TJSP,
    TribunalSession,
)
from app.schemas.dossie import DocumentoDossieSchema, DossiePublicSchema, RoteiroSchema
from app.services.dossie_leitura import (
    PAUSA_ENTRE_DOCUMENTOS_SEGUNDOS,
    classificar_documento,
    linha_do_tempo_curta,
)
from app.services.esaj_http import (
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
    montar_client,
)
from app.services.esaj_pasta import (
    PecaPasta,
    abrir_pasta,
    baixar_pdf_pasta,
    carregar_pecas,
    links_de_lista,
)
from app.services.pdf_texto import extrair_texto_pdf_async
from app.services.dossie_prompt import (
    RESUMO_SEM_TEXTO,
    fingerprint_fichas,
    montar_mensagem_dossie,
    montar_mensagem_ficha,
)
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMAutenticacaoError, LLMLimiteAtingidoError

logger = logging.getLogger(__name__)

MENSAGEM_IA_RECUSADA = (
    "Os PDFs abriram e o texto foi extraído. A chave da IA no OpenRouter expirou, "
    "então o resumo não foi gerado. Crie outra chave, coloque em OPENROUTER_API_KEY "
    "no backend e clique em Ler de novo."
)

MAX_INICIOS_HORA = 10
_JANELA_SEGUNDOS = 3600

_mutex = asyncio.Lock()
_processos: set[UUID] = set()
_usuarios: dict[UUID, UUID] = {}
_inicios: dict[UUID, list[float]] = {}


class LeituraEmAndamentoError(Exception):
    """Já existe uma leitura deste processo ou deste usuário."""


class LimiteLeituraError(Exception):
    """O usuário passou do teto de leituras na última hora."""


def limpar_controle_leitura() -> None:
    """Só testes. Zera a trava em memória deste processo."""
    _processos.clear()
    _usuarios.clear()
    _inicios.clear()


def leitura_em_andamento(processo_id: UUID) -> bool:
    return processo_id in _processos


async def reservar(user_id: UUID, processo_id: UUID) -> str | None:
    """`None` quando a vaga foi reservada. Caso contrário, o motivo."""
    async with _mutex:
        if processo_id in _processos or user_id in _usuarios:
            return "em_andamento"
        agora = time.monotonic()
        recentes = [t for t in _inicios.get(user_id, []) if agora - t < _JANELA_SEGUNDOS]
        if len(recentes) >= MAX_INICIOS_HORA:
            _inicios[user_id] = recentes
            return "limite"
        recentes.append(agora)
        _inicios[user_id] = recentes
        _processos.add(processo_id)
        _usuarios[user_id] = processo_id
        return None


async def liberar(user_id: UUID, processo_id: UUID) -> None:
    async with _mutex:
        _processos.discard(processo_id)
        if _usuarios.get(user_id) == processo_id:
            del _usuarios[user_id]


def select_processo_do_usuario(user_id: UUID, processo_id: UUID):
    return select(Processo).where(Processo.id == processo_id, Processo.user_id == user_id)


def cifrar_ficha(texto: str) -> bytes:
    return encrypt_secret(texto)


def _decrypt_opcional(blob: bytes | None) -> str | None:
    if blob is None:
        return None
    try:
        return decrypt_secret(blob)
    except DecriptografiaError:
        return None


async def _movimentos(db: AsyncSession, user_id: UUID, processo_id: UUID) -> list[Movimentacao]:
    return list(
        (
            await db.scalars(
                select(Movimentacao)
                .join(Processo, Movimentacao.processo_id == Processo.id)
                .where(
                    Processo.id == processo_id,
                    Processo.user_id == user_id,
                    Movimentacao.tem_documento.is_(True),
                )
                .order_by(Movimentacao.data_movimentacao.desc().nulls_last())
            )
        ).all()
    )


def _pecas_do_blob(blob: bytes | None) -> list[dict]:
    texto = _decrypt_opcional(blob)
    if not texto:
        return []
    try:
        bruto = json.loads(texto)
    except json.JSONDecodeError:
        return []
    if not isinstance(bruto, list):
        return []
    return [item for item in bruto if isinstance(item, dict)]


def _gravar_pecas(dossie: ProcessoDossie, pecas: list[dict]) -> None:
    dossie.pecas_encrypted = cifrar_ficha(json.dumps(pecas, ensure_ascii=False))


def _documentos_das_pecas(processo_id: UUID, pecas: list[dict]) -> list[DocumentoDossieSchema]:
    documentos: list[DocumentoDossieSchema] = []
    for indice, peca in enumerate(pecas):
        status = peca.get("status")
        documentos.append(
            DocumentoDossieSchema(
                movimentacao_id=uuid5(NAMESPACE_URL, f"{processo_id}:{indice}"),
                titulo=peca.get("titulo") if isinstance(peca.get("titulo"), str) else None,
                data=None,
                status=status if isinstance(status, str) else STATUS_DOC_PENDENTE,
            )
        )
    return documentos


def _roteiro_do_blob(blob: bytes | None) -> RoteiroSchema:
    texto = _decrypt_opcional(blob)
    if not texto:
        return RoteiroSchema()
    try:
        return RoteiroSchema.model_validate_json(texto)
    except ValueError:
        return RoteiroSchema()


def _contagem(pecas: list[dict]) -> tuple[int, int]:
    lidos = sum(1 for peca in pecas if peca.get("status") in STATUS_DOC_TERMINAIS)
    return lidos, len(pecas)


async def obter_dossie(
    db: AsyncSession, user_id: UUID, processo_id: UUID
) -> DossiePublicSchema | None:
    processo = await db.scalar(select_processo_do_usuario(user_id, processo_id))
    if processo is None:
        return None

    dossie = await db.scalar(
        select(ProcessoDossie).where(
            ProcessoDossie.processo_id == processo_id,
            ProcessoDossie.user_id == user_id,
        )
    )
    if dossie is None:
        return DossiePublicSchema(
            processo_id=processo_id,
            status="ocioso",
            lidos=0,
            total=0,
            documentos=[],
        )
    pecas = _pecas_do_blob(dossie.pecas_encrypted)
    if pecas:
        lidos, total = _contagem(pecas)
    elif dossie.status == STATUS_DOSSIE_LENDO:
        lidos, total = dossie.lidos, dossie.total
    else:
        lidos, total = 0, 0
    return DossiePublicSchema(
        processo_id=processo_id,
        status=dossie.status,
        lidos=lidos,
        total=total,
        gerado_em=dossie.gerado_em,
        retomar_apos=dossie.retomar_apos,
        resumo=_decrypt_opcional(dossie.resumo_encrypted),
        roteiro=_roteiro_do_blob(dossie.roteiro_encrypted),
        documentos=_documentos_das_pecas(processo_id, pecas),
    )


async def salvar_roteiro(
    db: AsyncSession, user_id: UUID, processo_id: UUID, roteiro: RoteiroSchema
) -> DossiePublicSchema | None:
    """Grava o roteiro cifrado. Processo de outro advogado devolve None."""
    processo = await db.scalar(select_processo_do_usuario(user_id, processo_id))
    if processo is None:
        return None
    dossie = await db.scalar(
        select(ProcessoDossie).where(
            ProcessoDossie.processo_id == processo_id,
            ProcessoDossie.user_id == user_id,
        )
    )
    if dossie is None:
        dossie = ProcessoDossie(
            user_id=user_id,
            processo_id=processo_id,
            status=STATUS_DOSSIE_OCIOSO,
        )
        db.add(dossie)
    dossie.roteiro_encrypted = cifrar_ficha(roteiro.model_dump_json())
    await db.commit()
    return await obter_dossie(db, user_id, processo_id)


async def _marcar_lendo(db: AsyncSession, user_id: UUID, processo_id: UUID) -> None:
    dossie = await db.scalar(
        select(ProcessoDossie).where(
            ProcessoDossie.processo_id == processo_id,
            ProcessoDossie.user_id == user_id,
        )
    )
    if dossie is None:
        db.add(
            ProcessoDossie(
                user_id=user_id,
                processo_id=processo_id,
                status=STATUS_DOSSIE_LENDO,
                lidos=0,
                total=0,
            )
        )
    else:
        dossie.status = STATUS_DOSSIE_LENDO
        dossie.retomar_apos = None
    await db.commit()


def agendar_leitura(user_id: UUID, processo_id: UUID) -> None:
    asyncio.create_task(_tarefa(user_id, processo_id))


async def iniciar_leitura(
    db: AsyncSession, user_id: UUID, processo_id: UUID
) -> DossiePublicSchema | None:
    """`None` se o processo não é do usuário.

    Levanta `LeituraEmAndamentoError` ou `LimiteLeituraError`.
    """
    processo = await db.scalar(select_processo_do_usuario(user_id, processo_id))
    if processo is None:
        return None
    codigo = await reservar(user_id, processo_id)
    if codigo == "em_andamento":
        raise LeituraEmAndamentoError(str(processo_id))
    if codigo == "limite":
        raise LimiteLeituraError(str(user_id))
    try:
        await _marcar_lendo(db, user_id, processo_id)
        agendar_leitura(user_id, processo_id)
    except Exception:
        await liberar(user_id, processo_id)
        raise
    return await obter_dossie(db, user_id, processo_id)


async def _tarefa(user_id: UUID, processo_id: UUID) -> None:
    try:
        async with SessionLocal() as db:
            await executar_leitura(db, user_id, processo_id)
    except Exception as exc:
        logger.info("Leitura de autos falhou (causa=%s)", type(exc).__name__)
        try:
            async with SessionLocal() as db:
                await _marcar_erro_se_lendo(db, user_id, processo_id)
        except Exception as falha:
            logger.info(
                "Nao foi possivel gravar o erro da leitura (causa=%s)",
                type(falha).__name__,
            )
    finally:
        await liberar(user_id, processo_id)


async def _marcar_erro_se_lendo(db: AsyncSession, user_id: UUID, processo_id: UUID) -> None:
    dossie = await db.scalar(
        select(ProcessoDossie).where(
            ProcessoDossie.processo_id == processo_id,
            ProcessoDossie.user_id == user_id,
        )
    )
    if dossie is not None and dossie.status == STATUS_DOSSIE_LENDO:
        dossie.status = STATUS_DOSSIE_ERRO
        await db.commit()


def _aplicar_rate_limit(sessao: TribunalSession) -> None:
    sessao.status = SESSION_STATUS_BLOQUEADO
    sessao.tentativas_falha += 1
    sessao.proximo_retry = calcular_proximo_retry(sessao.tentativas_falha)


async def _consolidar(
    dossie: ProcessoDossie,
    *,
    movs: list[Movimentacao],
    fichas: list[str],
) -> str | None:
    """`limite_ia` ou `erro` quando a consolidação não termina. Senão, None."""
    if not fichas:
        texto = RESUMO_SEM_TEXTO
        material = [texto]
    else:
        texto = None
        material = fichas

    novo = fingerprint_fichas(material)
    if dossie.fingerprint == novo and dossie.resumo_encrypted is not None:
        return None

    if fichas:
        linha = linha_do_tempo_curta(
            [(mov.data_movimentacao, mov.titulo, mov.descricao) for mov in movs]
        )
        try:
            texto = await get_llm_provider().consolidar_dossie(
                fichas=tuple(fichas), linha_do_tempo=linha
            )
        except LLMLimiteAtingidoError:
            return "limite_ia"
        except Exception as exc:
            logger.info("Consolidar dossie falhou (causa=%s)", type(exc).__name__)
            return "erro"

    if texto:
        dossie.resumo_encrypted = cifrar_ficha(texto)
        dossie.fingerprint = novo
        dossie.gerado_em = datetime.now(UTC)
    return None


def _fichas_das_pecas(pecas: list[dict]) -> list[str]:
    fichas: list[str] = []
    for peca in pecas:
        ficha = peca.get("ficha")
        if isinstance(ficha, str) and ficha.strip():
            fichas.append(ficha)
    return fichas


async def _ler_pecas_da_pasta(
    db: AsyncSession,
    *,
    dossie: ProcessoDossie,
    sessao: TribunalSession,
    user_id: UUID,
    processo_id: UUID,
    url_pasta: str,
    referer: str,
    movs: list[Movimentacao],
) -> str | None:
    """Baixa as peças da pasta. Não apaga o cookie se o CAS pedir login."""
    if sessao.cookie_encrypted is None:
        return "sessao_expirada"
    bruto: dict | list | None = None
    try:
        try:
            carregado = json.loads(decrypt_secret(sessao.cookie_encrypted))
        except (DecriptografiaError, ValueError):
            return "sessao_expirada"
        if not isinstance(carregado, (dict, list)):
            return "sessao_expirada"
        bruto = carregado

        async with montar_client(bruto) as client:
            try:
                aberta = await abrir_pasta(client, url_pasta, referer=referer)
            except EsajSessaoInvalidaError:
                return "sessao_expirada"
            except EsajRateLimitError:
                _aplicar_rate_limit(sessao)
                dossie.retomar_apos = sessao.proximo_retry
                return "bloqueado"
            except EsajPortalIndisponivelError:
                return "erro"

            if aberta.pdf:
                pecas_portal = [PecaPasta(titulo="Autos", url="")]
            else:
                try:
                    pecas_portal = await carregar_pecas(client, aberta.html, referer=referer)
                except EsajSessaoInvalidaError:
                    return "sessao_expirada"
            if not pecas_portal and not aberta.pdf:
                logger.info(
                    "Pasta sem lista de PDFs (caminhos=%s)",
                    ",".join(links_de_lista(aberta.html)) or "-",
                )
                return "sem_lista"

            provider = get_llm_provider()
            try:
                await provider.resumir_documento(
                    texto="Confirmacao de acesso.", titulo=None, data=None
                )
            except LLMAutenticacaoError:
                return "ia_recusada"
            guardadas = _pecas_do_blob(dossie.pecas_encrypted)
            pecas: list[dict] = []

            async def extrair(dados: bytes):
                return await extrair_texto_pdf_async(dados, max_paginas=80, max_paginas_ocr=12)

            async def resumir(texto: str, titulo: str | None, data: str | None) -> str:
                return await provider.resumir_documento(texto=texto, titulo=titulo, data=data)

            pdf_em_memoria = aberta.pdf

            async def baixar(url: str) -> bytes:
                if pdf_em_memoria:
                    return pdf_em_memoria
                return await baixar_pdf_pasta(client, url)

            for indice, peca in enumerate(pecas_portal):
                anterior = guardadas[indice] if indice < len(guardadas) else None
                if (
                    anterior is not None
                    and anterior.get("status") in (STATUS_DOC_LIDO, STATUS_DOC_PARCIAL)
                    and isinstance(anterior.get("ficha"), str)
                ):
                    pecas.append(anterior)
                    continue
                resultado = await classificar_documento(
                    url=peca.url or "https://esaj.tjsp.jus.br/pastadigital/getPDF.do",
                    titulo=peca.titulo,
                    data=None,
                    status_anterior=None,
                    url_hash_anterior=None,
                    baixar=baixar,
                    extrair=extrair,
                    resumir=resumir,
                )
                if resultado.parar == "sessao_expirada":
                    return "sessao_expirada"
                if resultado.parar == "bloqueado":
                    _aplicar_rate_limit(sessao)
                    dossie.retomar_apos = sessao.proximo_retry
                    return "bloqueado"
                if resultado.parar == "limite_ia":
                    return "limite_ia"
                if resultado.parar == "ia_recusada":
                    return "ia_recusada"
                pecas.append(
                    {
                        "titulo": peca.titulo,
                        "status": resultado.status,
                        "paginas": resultado.paginas,
                        "ficha": resultado.ficha,
                    }
                )
                _gravar_pecas(dossie, pecas)
                dossie.lidos, dossie.total = _contagem(pecas)
                await db.commit()
                if resultado.baixou and indice < len(pecas_portal) - 1:
                    await asyncio.sleep(PAUSA_ENTRE_DOCUMENTOS_SEGUNDOS)
            pdf_em_memoria = b""
            aberta = None
    finally:
        bruto = None

    fichas = _fichas_das_pecas(_pecas_do_blob(dossie.pecas_encrypted))
    return await _consolidar(dossie, movs=movs, fichas=fichas)


async def executar_leitura(db: AsyncSession, user_id: UUID, processo_id: UUID) -> None:
    dossie = await db.scalar(
        select(ProcessoDossie).where(
            ProcessoDossie.processo_id == processo_id,
            ProcessoDossie.user_id == user_id,
        )
    )
    if dossie is None:
        return

    processo = await db.scalar(select_processo_do_usuario(user_id, processo_id))
    if processo is None or not processo.url_pasta:
        dossie.status = STATUS_DOSSIE_SEM
        dossie.lidos = 0
        dossie.total = 0
        await db.commit()
        return

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
        if sessao is not None and sessao.status == SESSION_STATUS_BLOQUEADO:
            dossie.status = STATUS_DOSSIE_BLOQUEADO
            dossie.retomar_apos = sessao.proximo_retry
        else:
            dossie.status = STATUS_DOSSIE_SESSAO
        await db.commit()
        return

    movs = await _movimentos(db, user_id, processo_id)
    referer = processo.url_cpo or "https://esaj.tjsp.jus.br/cpopg/open.do"
    parar = await _ler_pecas_da_pasta(
        db,
        dossie=dossie,
        sessao=sessao,
        user_id=user_id,
        processo_id=processo_id,
        url_pasta=processo.url_pasta,
        referer=referer,
        movs=movs,
    )
    if parar == "limite_ia":
        dossie.status = STATUS_DOSSIE_LIMITE
    elif parar == "bloqueado":
        dossie.status = STATUS_DOSSIE_BLOQUEADO
    elif parar == "sessao_expirada":
        dossie.status = STATUS_DOSSIE_SESSAO
    elif parar == "sem_lista":
        dossie.status = STATUS_DOSSIE_ERRO
        dossie.resumo_encrypted = cifrar_ficha(
            "A pasta abriu, mas a lista de PDFs não veio. Nada foi lido."
        )
    elif parar == "erro":
        dossie.status = STATUS_DOSSIE_ERRO
    elif parar == "ia_recusada":
        dossie.status = STATUS_DOSSIE_ERRO
        dossie.resumo_encrypted = cifrar_ficha(MENSAGEM_IA_RECUSADA)
    else:
        dossie.status = STATUS_DOSSIE_PRONTO
    pecas = _pecas_do_blob(dossie.pecas_encrypted)
    if pecas:
        dossie.lidos, dossie.total = _contagem(pecas)
    await db.commit()


async def contexto_de_autos(
    db: AsyncSession, user_id: UUID, processo_id: UUID
) -> tuple[str | None, tuple[str, ...]]:
    """Resumo do dossiê e linha do tempo curta para o redator."""
    dossie = await db.scalar(
        select(ProcessoDossie).where(
            ProcessoDossie.processo_id == processo_id,
            ProcessoDossie.user_id == user_id,
        )
    )
    resumo = _decrypt_opcional(dossie.resumo_encrypted) if dossie is not None else None
    movs = (
        await db.scalars(
            select(Movimentacao)
            .join(Processo, Movimentacao.processo_id == Processo.id)
            .where(Processo.id == processo_id, Processo.user_id == user_id)
            .order_by(Movimentacao.data_movimentacao.desc().nulls_last())
            .limit(40)
        )
    ).all()
    linha = linha_do_tempo_curta(
        [(mov.data_movimentacao, mov.titulo, mov.descricao) for mov in movs]
    )
    return resumo, linha


def mensagem_ficha_para_provedor(*, texto: str, titulo: str | None, data: str | None) -> str:
    return montar_mensagem_ficha(texto=texto, titulo=titulo, data=data)


def mensagem_dossie_para_provedor(
    *, fichas: tuple[str, ...], linha_do_tempo: tuple[str, ...]
) -> str:
    return montar_mensagem_dossie(fichas=list(fichas), linha_do_tempo=list(linha_do_tempo))
