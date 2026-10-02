"""Serviço da IA da elaboração (ADR-016).

Toda consulta filtra `WHERE user_id = current_user.id` no banco — nunca
filtra em Python depois de buscar tudo. Fatos extras, instrução e conteúdo
da minuta são descriptografados só em memória, no momento do uso, e
descartados ao final da função (nunca em atributo de classe ou cache).
"""

import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import DecriptografiaError, decrypt_secret, encrypt_secret
from app.models.elaboracao import (
    ORIGEM_CHAT,
    ORIGEM_GERACAO,
    ORIGEM_GRIFO,
    Elaboracao,
    ElaboracaoVersao,
)
from app.models.intimacao import Intimacao
from app.models.movimentacao import Movimentacao
from app.models.processo import Processo
from app.schemas.elaboracao import (
    ElaboracaoPublicSchema,
    SugestaoPecaSchema,
    VersaoMinutaPublicSchema,
)
from app.services.elaboracao_pecas import PECAS_IDS_VALIDOS
from app.services.elaboracao_prompt import montar_contexto_elaboracao
from app.services.llm import get_llm_provider
from app.services.llm.base import LLMLimiteAtingidoError
from app.services.llm.contexto import SinaisSugestaoPeca

# Depois de um 429, a sugestão automática (abre ao carregar a ficha) fica
# em pausa. Elaborar, chat e grifo continuam sob demanda — são o que o
# advogado clicou de propósito.
_PAUSA_SUGESTAO_SEGUNDOS = 600
_sugestao_pausada_ate = 0.0


class SemVersaoAnteriorError(Exception):
    """Chat/grifo pedido antes de existir qualquer versão gerada."""


class VersaoIlegivelError(Exception):
    """A última versão existe, mas o conteúdo não decripta com a chave atual."""


def sugestao_em_pausa(agora: float | None = None) -> bool:
    return (agora if agora is not None else time.monotonic()) < _sugestao_pausada_ate


def pausar_sugestao_automatica(agora: float | None = None) -> None:
    global _sugestao_pausada_ate
    instante = agora if agora is not None else time.monotonic()
    _sugestao_pausada_ate = instante + _PAUSA_SUGESTAO_SEGUNDOS


def retomar_sugestao_automatica() -> None:
    """Só para testes — zera a pausa deixada por um 429 anterior."""
    global _sugestao_pausada_ate
    _sugestao_pausada_ate = 0.0


def _decrypt_opcional(blob: bytes | None) -> str | None:
    if blob is None:
        return None
    try:
        return decrypt_secret(blob)
    except DecriptografiaError:
        # Nunca deixa o request 500 por um blob corrompido — melhor "sumir"
        # o texto do que travar a tela de elaboração.
        return None


def _elaboracao_publica(elaboracao: Elaboracao) -> ElaboracaoPublicSchema:
    return ElaboracaoPublicSchema(
        id=elaboracao.id,
        processo_id=elaboracao.processo_id,
        peca=elaboracao.peca,
        fatos_extras=_decrypt_opcional(elaboracao.fatos_extras_encrypted),
        estilo_perfil=_decrypt_opcional(elaboracao.estilo_perfil_encrypted),
        created_at=elaboracao.created_at,
        updated_at=elaboracao.updated_at,
    )


def _versao_publica(versao: ElaboracaoVersao) -> VersaoMinutaPublicSchema:
    return VersaoMinutaPublicSchema(
        id=versao.id,
        origem=versao.origem,
        instrucao=_decrypt_opcional(versao.instrucao_encrypted),
        trecho_selecionado=_decrypt_opcional(versao.trecho_alvo_encrypted),
        conteudo_html=_decrypt_opcional(versao.conteudo_encrypted) or "",
        llm_provider=versao.llm_provider,
        llm_model=versao.llm_model,
        criado_em=versao.created_at,
    )


async def _buscar_elaboracao(
    db: AsyncSession, user_id: UUID, elaboracao_id: UUID
) -> Elaboracao | None:
    return await db.scalar(
        select(Elaboracao).where(Elaboracao.id == elaboracao_id, Elaboracao.user_id == user_id)
    )


async def obter_ou_criar_elaboracao(
    db: AsyncSession, user_id: UUID, *, processo_id: UUID, peca: str
) -> ElaboracaoPublicSchema | None:
    """`None` quando o `processo_id` não existe ou não é do usuário."""
    processo = await db.scalar(
        select(Processo).where(Processo.id == processo_id, Processo.user_id == user_id)
    )
    if processo is None:
        return None

    existente = await db.scalar(
        select(Elaboracao).where(
            Elaboracao.user_id == user_id,
            Elaboracao.processo_id == processo_id,
            Elaboracao.peca == peca,
        )
    )
    if existente is not None:
        return _elaboracao_publica(existente)

    nova = Elaboracao(user_id=user_id, processo_id=processo_id, peca=peca)
    db.add(nova)
    await db.commit()
    await db.refresh(nova)
    return _elaboracao_publica(nova)


async def atualizar_fatos_extras(
    db: AsyncSession, user_id: UUID, elaboracao_id: UUID, *, fatos_extras: str | None
) -> ElaboracaoPublicSchema | None:
    elaboracao = await _buscar_elaboracao(db, user_id, elaboracao_id)
    if elaboracao is None:
        return None

    texto = fatos_extras.strip() if fatos_extras else None
    elaboracao.fatos_extras_encrypted = encrypt_secret(texto) if texto else None
    await db.commit()
    await db.refresh(elaboracao)
    return _elaboracao_publica(elaboracao)


async def gerar_primeira_versao(
    db: AsyncSession, user_id: UUID, elaboracao_id: UUID
) -> VersaoMinutaPublicSchema | None:
    elaboracao = await _buscar_elaboracao(db, user_id, elaboracao_id)
    if elaboracao is None:
        return None

    processo = await db.scalar(select(Processo).where(Processo.id == elaboracao.processo_id))
    if processo is None:
        # FK com ON DELETE CASCADE garante isso na prática — defensivo aqui.
        return None
    fatos_extras = _decrypt_opcional(elaboracao.fatos_extras_encrypted)
    estilo_perfil = _decrypt_opcional(elaboracao.estilo_perfil_encrypted)
    contexto = montar_contexto_elaboracao(
        processo, peca=elaboracao.peca, fatos_extras=fatos_extras, estilo_perfil=estilo_perfil
    )

    provider = get_llm_provider()
    html = await provider.gerar_minuta(contexto)

    versao = ElaboracaoVersao(
        elaboracao_id=elaboracao.id,
        origem=ORIGEM_GERACAO,
        conteudo_encrypted=encrypt_secret(html),
        llm_provider=provider.nome,
        llm_model=get_settings().llm_model or None,
    )
    db.add(versao)
    await db.commit()
    await db.refresh(versao)
    return _versao_publica(versao)


async def registrar_edicao(
    db: AsyncSession,
    user_id: UUID,
    elaboracao_id: UUID,
    *,
    instrucao: str,
    trecho_selecionado: str | None,
) -> VersaoMinutaPublicSchema | None:
    """`None` se a elaboração não existe/não é do usuário.

    Levanta `SemVersaoAnteriorError` se ainda não há nenhuma versão gerada
    (o advogado precisa clicar Elaborar antes de conversar/grifar).
    Levanta `VersaoIlegivelError` se a última versão não decripta — não chama
    o modelo com HTML vazio.
    """
    elaboracao = await _buscar_elaboracao(db, user_id, elaboracao_id)
    if elaboracao is None:
        return None

    ultima = await db.scalar(
        select(ElaboracaoVersao)
        .where(ElaboracaoVersao.elaboracao_id == elaboracao.id)
        .order_by(ElaboracaoVersao.created_at.desc())
        .limit(1)
    )
    if ultima is None:
        raise SemVersaoAnteriorError(str(elaboracao.id))

    html_atual = _decrypt_opcional(ultima.conteudo_encrypted)
    if html_atual is None:
        raise VersaoIlegivelError(str(elaboracao.id))

    provider = get_llm_provider()
    trecho = trecho_selecionado.strip() if trecho_selecionado else None
    html_novo = await provider.editar_minuta(
        html_atual=html_atual, instrucao=instrucao, trecho_selecionado=trecho
    )

    versao = ElaboracaoVersao(
        elaboracao_id=elaboracao.id,
        origem=ORIGEM_GRIFO if trecho else ORIGEM_CHAT,
        instrucao_encrypted=encrypt_secret(instrucao.strip()),
        trecho_alvo_encrypted=encrypt_secret(trecho) if trecho else None,
        conteudo_encrypted=encrypt_secret(html_novo),
        llm_provider=provider.nome,
        llm_model=get_settings().llm_model or None,
    )
    db.add(versao)
    await db.commit()
    await db.refresh(versao)
    return _versao_publica(versao)


async def listar_versoes(
    db: AsyncSession, user_id: UUID, elaboracao_id: UUID
) -> list[VersaoMinutaPublicSchema] | None:
    """`None` se a elaboração não existe/não é do usuário; `[]` se ainda não
    há versão gerada."""
    elaboracao = await _buscar_elaboracao(db, user_id, elaboracao_id)
    if elaboracao is None:
        return None

    versoes = (
        await db.scalars(
            select(ElaboracaoVersao)
            .where(ElaboracaoVersao.elaboracao_id == elaboracao.id)
            .order_by(ElaboracaoVersao.created_at.desc())
        )
    ).all()
    return [_versao_publica(versao) for versao in versoes]


async def sugerir_peca_para_processo(
    db: AsyncSession, user_id: UUID, processo_id: UUID
) -> SugestaoPecaSchema | None:
    """`None` só quando o processo não existe/não é do usuário (→ 404 na
    rota). Sem sinal suficiente, devolve `SugestaoPecaSchema(peca=None)` —
    não é erro, é "sem palpite" (ADR-016 Fase 1, select continua livre)."""
    processo = await db.scalar(
        select(Processo).where(Processo.id == processo_id, Processo.user_id == user_id)
    )
    if processo is None:
        return None

    if sugestao_em_pausa():
        return SugestaoPecaSchema(peca=None, explicacao=None)

    ultima_intimacao = await db.scalar(
        select(Intimacao)
        .where(Intimacao.user_id == user_id, Intimacao.processo_id == processo_id)
        .order_by(Intimacao.data_movimentacao.desc())
        .limit(1)
    )
    ultima_movimentacao = await db.scalar(
        select(Movimentacao)
        .join(Processo, Movimentacao.processo_id == Processo.id)
        .where(Processo.id == processo_id, Processo.user_id == user_id)
        .order_by(Movimentacao.data_movimentacao.desc())
        .limit(1)
    )

    sinais = SinaisSugestaoPeca(
        classe=processo.de_classe,
        assunto=processo.de_assunto,
        ultima_intimacao_titulo=ultima_intimacao.titulo if ultima_intimacao else None,
        ultima_movimentacao_titulo=ultima_movimentacao.titulo if ultima_movimentacao else None,
    )

    try:
        sugestao = await get_llm_provider().sugerir_peca(sinais)
    except LLMLimiteAtingidoError:
        pausar_sugestao_automatica()
        return SugestaoPecaSchema(peca=None, explicacao=None)
    if sugestao is None or sugestao.peca not in PECAS_IDS_VALIDOS:
        # Provider sugeriu id fora do catálogo (ou nenhum) — não propaga
        # lixo ao frontend, trata como "sem sugestão".
        return SugestaoPecaSchema(peca=None, explicacao=None)
    return SugestaoPecaSchema(peca=sugestao.peca, explicacao=sugestao.explicacao)


async def definir_estilo_por_texto(
    db: AsyncSession, user_id: UUID, elaboracao_id: UUID, *, texto: str
) -> ElaboracaoPublicSchema | None:
    """`None` se a elaboração não existe/não é do usuário (→ 404 na rota)."""
    elaboracao = await _buscar_elaboracao(db, user_id, elaboracao_id)
    if elaboracao is None:
        return None

    perfil_json = await get_llm_provider().extrair_perfil_estilo(texto_amostra=texto.strip())
    elaboracao.estilo_perfil_encrypted = encrypt_secret(perfil_json)
    await db.commit()
    await db.refresh(elaboracao)
    return _elaboracao_publica(elaboracao)
