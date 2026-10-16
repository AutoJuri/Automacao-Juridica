"""Capa das elaborações do usuário.

Toda leitura e escrita filtra `user_id` no banco. Processo ou elaboração de
outra pessoa responde 404. O texto da minuta não passa por aqui.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audiencia import Audiencia
from app.models.elaboracao import PECAS, Elaboracao
from app.models.intimacao import Intimacao
from app.models.processo import Processo
from app.schemas.elaboracao import (
    ElaboracaoCardSchema,
    ElaboracaoCreateSchema,
    ElaboracaoDetalheSchema,
    ElaboracaoManualSchema,
    ElaboracaoUpdateSchema,
    PaginaProcessosParaIniciarSchema,
    ProcessoParaIniciarSchema,
)
from app.services.painel import montar_ultima_atividade

LIMITE_EM_ANDAMENTO = 100
LIMITE_A_INICIAR = 12

_NAO_ENCONTRADA = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Elaboração não encontrada",
)
_PROCESSO_NAO_ENCONTRADO = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Processo não encontrado",
)
_PECA_REPETIDA = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Já existe uma elaboração dessa peça neste processo",
)
_USA_PROCESSO = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Essa elaboração usa os dados do processo",
)


def _nome_parte(parte: dict | None) -> str | None:
    if not parte:
        return None
    nome = parte.get("nome") or parte.get("nomeSocial")
    if isinstance(nome, str) and nome.strip():
        return nome.strip()
    return None


def _card(elaboracao: Elaboracao) -> ElaboracaoCardSchema:
    processo = elaboracao.processo
    if processo is not None:
        return ElaboracaoCardSchema(
            id=elaboracao.id,
            peca=elaboracao.peca,
            rotulo=PECAS[elaboracao.peca],
            titulo=None,
            nu_processo=processo.nu_processo,
            autor=_nome_parte(processo.parte_ativa),
            reu=_nome_parte(processo.parte_passiva),
            tem_processo=True,
            updated_at=elaboracao.updated_at,
        )
    return ElaboracaoCardSchema(
        id=elaboracao.id,
        peca=elaboracao.peca,
        rotulo=PECAS[elaboracao.peca],
        titulo=elaboracao.titulo,
        nu_processo=elaboracao.nu_processo,
        autor=elaboracao.parte_ativa,
        reu=elaboracao.parte_passiva,
        tem_processo=False,
        updated_at=elaboracao.updated_at,
    )


def _manual(elaboracao: Elaboracao) -> ElaboracaoManualSchema | None:
    if elaboracao.processo_id is not None or elaboracao.titulo is None:
        return None
    return ElaboracaoManualSchema(
        titulo=elaboracao.titulo,
        nu_processo=elaboracao.nu_processo,
        parte_ativa=elaboracao.parte_ativa,
        parte_passiva=elaboracao.parte_passiva,
        classe=elaboracao.classe,
        assunto=elaboracao.assunto,
        foro_vara=elaboracao.foro_vara,
        valor_causa=elaboracao.valor_causa,
        juiz=elaboracao.juiz,
    )


def _detalhe(elaboracao: Elaboracao) -> ElaboracaoDetalheSchema:
    return ElaboracaoDetalheSchema(
        **_card(elaboracao).model_dump(),
        processo_id=elaboracao.processo_id,
        manual=_manual(elaboracao),
    )


async def _por_id(db: AsyncSession, user_id: UUID, elaboracao_id: UUID) -> Elaboracao:
    elaboracao = await db.scalar(
        select(Elaboracao)
        .where(Elaboracao.id == elaboracao_id, Elaboracao.user_id == user_id)
        .options(selectinload(Elaboracao.processo))
    )
    if elaboracao is None:
        raise _NAO_ENCONTRADA
    return elaboracao


def _filtro_busca_elaboracao(user_id: UUID, termo: str):
    like = f"%{termo}%"
    return or_(
        Elaboracao.titulo.ilike(like),
        Elaboracao.nu_processo.ilike(like),
        Elaboracao.parte_ativa.ilike(like),
        Elaboracao.parte_passiva.ilike(like),
        Elaboracao.processo_id.in_(
            select(Processo.id).where(
                Processo.user_id == user_id,
                or_(
                    Processo.nu_processo.ilike(like),
                    Processo.de_classe.ilike(like),
                    Processo.parte_ativa["nome"].astext.ilike(like),
                    Processo.parte_passiva["nome"].astext.ilike(like),
                ),
            )
        ),
    )


async def listar_em_andamento(
    db: AsyncSession, user_id: UUID, *, q: str | None
) -> list[ElaboracaoCardSchema]:
    filtros = [Elaboracao.user_id == user_id]
    termo = (q or "").strip()
    if termo:
        filtros.append(_filtro_busca_elaboracao(user_id, termo))
    elaboracoes = list(
        (
            await db.scalars(
                select(Elaboracao)
                .where(*filtros)
                .options(selectinload(Elaboracao.processo))
                .order_by(Elaboracao.updated_at.desc())
                .limit(LIMITE_EM_ANDAMENTO)
            )
        ).all()
    )
    return [_card(item) for item in elaboracoes]


def _busca_processo(termo: str):
    like = f"%{termo}%"
    return or_(
        Processo.nu_processo.ilike(like),
        Processo.de_classe.ilike(like),
        Processo.de_assunto.ilike(like),
        Processo.parte_ativa["nome"].astext.ilike(like),
        Processo.parte_passiva["nome"].astext.ilike(like),
    )


async def listar_a_iniciar(
    db: AsyncSession, user_id: UUID, *, offset: int, q: str | None
) -> PaginaProcessosParaIniciarSchema:
    ja_comecou = (
        select(Elaboracao.id)
        .where(
            Elaboracao.processo_id == Processo.id,
            Elaboracao.user_id == user_id,
        )
        .exists()
    )
    filtros = [Processo.user_id == user_id, ~ja_comecou]
    termo = (q or "").strip()
    if termo:
        filtros.append(_busca_processo(termo))
    total = await db.scalar(select(func.count()).select_from(Processo).where(*filtros))
    processos = list(
        (
            await db.scalars(
                select(Processo)
                .where(*filtros)
                .order_by(Processo.last_synced_at.desc().nulls_last(), Processo.created_at.desc())
                .offset(offset)
                .limit(LIMITE_A_INICIAR)
            )
        ).all()
    )
    return PaginaProcessosParaIniciarSchema(
        items=await _para_iniciar(db, user_id, processos),
        total=int(total or 0),
    )


async def _para_iniciar(
    db: AsyncSession, user_id: UUID, processos: list[Processo]
) -> list[ProcessoParaIniciarSchema]:
    if not processos:
        return []
    ids = [item.id for item in processos]
    intimacoes = list(
        (
            await db.scalars(
                select(Intimacao).where(
                    Intimacao.user_id == user_id,
                    Intimacao.processo_id.in_(ids),
                )
            )
        ).all()
    )
    audiencias = list(
        (
            await db.scalars(
                select(Audiencia).where(
                    Audiencia.user_id == user_id,
                    Audiencia.processo_id.in_(ids),
                )
            )
        ).all()
    )
    intimacoes_por: dict[UUID, list[Intimacao]] = {item.id: [] for item in processos}
    audiencias_por: dict[UUID, list[Audiencia]] = {item.id: [] for item in processos}
    for item in intimacoes:
        if item.processo_id is not None:
            intimacoes_por.setdefault(item.processo_id, []).append(item)
    for item in audiencias:
        if item.processo_id is not None:
            audiencias_por.setdefault(item.processo_id, []).append(item)
    return [
        ProcessoParaIniciarSchema(
            id=processo.id,
            nu_processo=processo.nu_processo,
            tribunal=processo.tribunal,
            classe=processo.de_classe,
            autor=_nome_parte(processo.parte_ativa),
            reu=_nome_parte(processo.parte_passiva),
            ultima_atividade=montar_ultima_atividade(
                intimacoes_por.get(processo.id, []),
                audiencias_por.get(processo.id, []),
            ),
        )
        for processo in processos
    ]


async def criar_ou_reabrir(
    db: AsyncSession, user_id: UUID, dados: ElaboracaoCreateSchema
) -> tuple[ElaboracaoDetalheSchema, bool]:
    if dados.processo_id is not None:
        processo = await db.scalar(
            select(Processo).where(Processo.id == dados.processo_id, Processo.user_id == user_id)
        )
        if processo is None:
            raise _PROCESSO_NAO_ENCONTRADO
        existente = await db.scalar(
            select(Elaboracao)
            .where(
                Elaboracao.user_id == user_id,
                Elaboracao.processo_id == dados.processo_id,
                Elaboracao.peca == dados.peca,
            )
            .options(selectinload(Elaboracao.processo))
        )
        if existente is not None:
            return _detalhe(existente), False
        elaboracao = Elaboracao(
            user_id=user_id,
            processo_id=dados.processo_id,
            peca=dados.peca,
        )
    else:
        manual = dados.manual
        assert manual is not None
        elaboracao = Elaboracao(
            user_id=user_id,
            peca=dados.peca,
            titulo=manual.titulo,
            nu_processo=manual.nu_processo,
            parte_ativa=manual.parte_ativa,
            parte_passiva=manual.parte_passiva,
            classe=manual.classe,
            assunto=manual.assunto,
            foro_vara=manual.foro_vara,
            valor_causa=manual.valor_causa,
            juiz=manual.juiz,
        )
    db.add(elaboracao)
    await db.commit()
    await db.refresh(elaboracao)
    elaboracao = await _por_id(db, user_id, elaboracao.id)
    return _detalhe(elaboracao), True


async def obter(
    db: AsyncSession, user_id: UUID, elaboracao_id: UUID
) -> ElaboracaoDetalheSchema:
    return _detalhe(await _por_id(db, user_id, elaboracao_id))


async def atualizar(
    db: AsyncSession,
    user_id: UUID,
    elaboracao_id: UUID,
    dados: ElaboracaoUpdateSchema,
) -> ElaboracaoDetalheSchema:
    elaboracao = await _por_id(db, user_id, elaboracao_id)
    if dados.manual is not None and elaboracao.processo_id is not None:
        raise _USA_PROCESSO
    if dados.peca is not None and dados.peca != elaboracao.peca:
        if elaboracao.processo_id is not None:
            conflito = await db.scalar(
                select(Elaboracao.id).where(
                    Elaboracao.user_id == user_id,
                    Elaboracao.processo_id == elaboracao.processo_id,
                    Elaboracao.peca == dados.peca,
                    Elaboracao.id != elaboracao.id,
                )
            )
            if conflito is not None:
                raise _PECA_REPETIDA
        elaboracao.peca = dados.peca
    if dados.manual is not None:
        manual = dados.manual
        elaboracao.titulo = manual.titulo
        elaboracao.nu_processo = manual.nu_processo
        elaboracao.parte_ativa = manual.parte_ativa
        elaboracao.parte_passiva = manual.parte_passiva
        elaboracao.classe = manual.classe
        elaboracao.assunto = manual.assunto
        elaboracao.foro_vara = manual.foro_vara
        elaboracao.valor_causa = manual.valor_causa
        elaboracao.juiz = manual.juiz
    elaboracao.updated_at = datetime.now(UTC)
    await db.commit()
    return _detalhe(await _por_id(db, user_id, elaboracao_id))


async def excluir(db: AsyncSession, user_id: UUID, elaboracao_id: UUID) -> None:
    elaboracao = await _por_id(db, user_id, elaboracao_id)
    await db.delete(elaboracao)
    await db.commit()
