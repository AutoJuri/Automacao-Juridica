"""Diff contra o banco e geração de notificações para os pipes de coleta.

`selecionar_novas_*` são funções puras (testáveis sem banco). O restante
faz I/O via SQLAlchemy — upsert de `Processo` e insert append-only de
`Intimacao`/`Audiencia`, seguido da criação das `Notification`
correspondentes só para o que é de fato novo.
"""

import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.etl import (
    audiencia_cpo_para_campos,
    audiencia_para_campos,
    capa_cpo_para_campos,
    intimacao_para_campos,
    montar_id_esaj_audiencia,
    movimentacao_para_campos,
    parse_datetime_esaj,
    partes_cpo_para_json,
    peticao_para_campos,
    processo_para_campos,
)
from app.models.audiencia import Audiencia
from app.models.audiencia_cpo import AudienciaCpo
from app.models.intimacao import Intimacao
from app.models.movimentacao import Movimentacao
from app.models.notification import (
    NOTIFICATION_TIPO_AUDIENCIA,
    NOTIFICATION_TIPO_INTIMACAO,
    NOTIFICATION_TIPO_MOVIMENTACAO,
    Notification,
)
from app.models.peticao_diversa import PeticaoDiversa
from app.models.processo import Processo
from app.models.tribunal import TRIBUNAL_ESAJ_TJSP
from app.schemas.esaj_cpo_raw import AudienciaCpoRaw, CpoDetalheRaw, MovimentacaoRaw, PeticaoDiversaRaw
from app.schemas.esaj_raw import AudienciaRaw, IntimacaoRaw, ProcessoRaw


def selecionar_novas_intimacoes(
    existentes: set[str], brutos: list[IntimacaoRaw]
) -> list[IntimacaoRaw]:
    return [raw for raw in brutos if raw.id not in existentes]


def selecionar_novas_audiencias(
    existentes: set[str], brutos_com_id: list[tuple[AudienciaRaw, str]]
) -> list[tuple[AudienciaRaw, str]]:
    return [item for item in brutos_com_id if item[1] not in existentes]


async def upsert_processos(
    db: AsyncSession, user_id: uuid.UUID, brutos: list[ProcessoRaw]
) -> dict[str, uuid.UUID]:
    """Upsert de ficha por `(user_id, cd_processo)`. `cdProcesso` pedido que
    não veio em `brutos` (omitido pelo e-SAJ) simplesmente não entra no
    mapa — quem chama trata isso como skip, não como falha.
    """
    if not brutos:
        return {}

    cds_processo = [raw.cd_processo for raw in brutos]
    resultado = await db.execute(
        select(Processo).where(Processo.user_id == user_id, Processo.cd_processo.in_(cds_processo))
    )
    existentes_por_cd = {p.cd_processo: p for p in resultado.scalars().all()}

    agora = datetime.now(UTC)
    processos_por_cd: dict[str, Processo] = {}
    for raw in brutos:
        campos = processo_para_campos(raw)
        processo = existentes_por_cd.get(raw.cd_processo)
        if processo is None:
            processo = Processo(user_id=user_id, tribunal=TRIBUNAL_ESAJ_TJSP, **campos)
            db.add(processo)
        else:
            for nome_campo, valor in campos.items():
                setattr(processo, nome_campo, valor)
        processo.last_synced_at = agora
        processos_por_cd[raw.cd_processo] = processo

    await db.flush()
    return {cd: processo.id for cd, processo in processos_por_cd.items()}


async def completar_processo_id_map(
    db: AsyncSession,
    user_id: uuid.UUID,
    cds_processo: set[str],
    mapa: dict[str, uuid.UUID],
) -> dict[str, uuid.UUID]:
    """Preenche `mapa` com o `processo_id` de fichas já persistidas para os
    `cdProcesso` que não vieram no upsert deste ciclo (ex.: o pipe de
    processos falhou, mas a ficha já existia de um ciclo anterior).
    """
    faltantes = [cd for cd in cds_processo if cd not in mapa]
    if not faltantes:
        return mapa

    resultado = await db.execute(
        select(Processo.cd_processo, Processo.id).where(
            Processo.user_id == user_id, Processo.cd_processo.in_(faltantes)
        )
    )
    for cd_processo, processo_id in resultado.all():
        mapa[cd_processo] = processo_id
    return mapa


async def diff_e_persistir_intimacoes(
    db: AsyncSession,
    user_id: uuid.UUID,
    brutos: list[IntimacaoRaw],
    processo_id_por_cd: dict[str, uuid.UUID],
) -> list[Intimacao]:
    if not brutos:
        return []

    ids_esaj = [raw.id for raw in brutos]
    resultado = await db.execute(
        select(Intimacao.id_esaj).where(Intimacao.user_id == user_id, Intimacao.id_esaj.in_(ids_esaj))
    )
    existentes = set(resultado.scalars().all())

    novas_raw = selecionar_novas_intimacoes(existentes, brutos)
    novas: list[Intimacao] = []
    for raw in novas_raw:
        campos = intimacao_para_campos(raw)
        intimacao = Intimacao(
            user_id=user_id,
            processo_id=processo_id_por_cd.get(raw.cd_processo),
            **campos,
        )
        db.add(intimacao)
        novas.append(intimacao)
    return novas


async def diff_e_persistir_audiencias(
    db: AsyncSession,
    user_id: uuid.UUID,
    brutos: list[AudienciaRaw],
    processo_id_por_cd: dict[str, uuid.UUID],
) -> list[Audiencia]:
    if not brutos:
        return []

    combos = [
        (raw, montar_id_esaj_audiencia(raw.cd_processo, parse_datetime_esaj(raw.data_audiencia), raw.titulo))
        for raw in brutos
    ]
    ids_esaj = [id_esaj for _, id_esaj in combos]
    resultado = await db.execute(
        select(Audiencia.id_esaj).where(Audiencia.user_id == user_id, Audiencia.id_esaj.in_(ids_esaj))
    )
    existentes = set(resultado.scalars().all())

    novas_combos = selecionar_novas_audiencias(existentes, combos)
    novas: list[Audiencia] = []
    for raw, id_esaj in novas_combos:
        campos = audiencia_para_campos(raw, id_esaj)
        audiencia = Audiencia(
            user_id=user_id,
            processo_id=processo_id_por_cd.get(raw.cd_processo),
            **campos,
        )
        db.add(audiencia)
        novas.append(audiencia)
    return novas


def _identidade_movimentacao(raw: MovimentacaoRaw) -> tuple[datetime, str] | None:
    """`None` quando a data não é parseável — nunca inventa data para
    conseguir persistir (ver `parse_data_movimentacao_cpo`)."""
    campos = movimentacao_para_campos(raw)
    data_movimentacao = campos["data_movimentacao"]
    if data_movimentacao is None:
        return None
    descricao_hash = hashlib.sha256(campos["descricao"].encode("utf-8")).hexdigest()
    return data_movimentacao, descricao_hash


def selecionar_novas_movimentacoes(
    existentes: set[tuple[datetime, str]],
    combos: list[tuple[MovimentacaoRaw, datetime, str]],
) -> list[tuple[MovimentacaoRaw, datetime, str]]:
    """Dedupe contra o banco **e** contra o próprio lote.

    O CPO lista a mesma movimentação mais de uma vez (mesmo dia + mesmo
    texto) — visto ao vivo, ex.: 3× "Documento Juntado" em 11/08/2026.
    Sem colapsar o lote, o INSERT estoura o unique e o commit inteiro
    some (nenhuma movimentação aparece no painel).
    """
    novas: list[tuple[MovimentacaoRaw, datetime, str]] = []
    vistos = set(existentes)
    for item in combos:
        chave = (item[1], item[2])
        if chave in vistos:
            continue
        vistos.add(chave)
        novas.append(item)
    return novas


async def diff_e_persistir_movimentacoes(
    db: AsyncSession,
    processo_id: uuid.UUID,
    brutos: list[MovimentacaoRaw],
) -> list[Movimentacao]:
    """Chave de dedupe `(processo_id, data_movimentacao, descricao_hash)` —
    mesmo unique do model `Movimentacao`. `descricao_hash` é calculado aqui
    com o mesmo algoritmo do `@validates` do model, só para comparar contra
    o banco antes do insert (a coluna em si continua sendo preenchida pelo
    validator na hora do `Movimentacao(...)`)."""
    if not brutos:
        return []

    combos: list[tuple[MovimentacaoRaw, datetime, str]] = []
    for raw in brutos:
        identidade = _identidade_movimentacao(raw)
        if identidade is None:
            continue
        combos.append((raw, identidade[0], identidade[1]))
    if not combos:
        return []

    hashes = [descricao_hash for _, _, descricao_hash in combos]
    resultado = await db.execute(
        select(Movimentacao).where(
            Movimentacao.processo_id == processo_id,
            Movimentacao.descricao_hash.in_(hashes),
        )
    )
    por_chave: dict[tuple[datetime, str], Movimentacao] = {}
    for mov in resultado.scalars():
        if mov.data_movimentacao is None:
            continue
        por_chave[(mov.data_movimentacao, mov.descricao_hash)] = mov

    vistos: set[tuple[datetime, str]] = set()
    for raw, data_movimentacao, descricao_hash in combos:
        chave = (data_movimentacao, descricao_hash)
        if chave in vistos:
            continue
        vistos.add(chave)
        existente = por_chave.get(chave)
        if existente is None:
            continue
        campos = movimentacao_para_campos(raw)
        existente.tem_documento = campos["tem_documento"]
        existente.url_documento = campos["url_documento"]

    existentes = set(por_chave)
    novas_combos = selecionar_novas_movimentacoes(existentes, combos)
    novas: list[Movimentacao] = []
    for raw, data_movimentacao, descricao_hash in novas_combos:
        campos = movimentacao_para_campos(raw)
        movimentacao = Movimentacao(processo_id=processo_id, **campos)
        db.add(movimentacao)
        novas.append(movimentacao)
        existentes.add((data_movimentacao, descricao_hash))
    return novas


def aplicar_complemento_cpo(processo: Processo, detalhe: CpoDetalheRaw) -> None:
    """Upsert da capa/partes/flags no processo já carregado. Não toca
    `de_classe` / `de_assunto` / polos JSON (fonte: API de processos).

    Campo de capa vazio no HTML **não apaga** valor já gravado. Lista de
    partes vazia no parse também não zera `partes_cpo` já preenchido.
    Flag `True` (empty state) não volta a `False` só porque o marcador
    sumiu do HTML; `None` (CPO ainda não passou) aceita o parse atual.
    """
    for nome, valor in capa_cpo_para_campos(detalhe.capa).items():
        if valor:
            setattr(processo, nome, valor)
    novas_partes = partes_cpo_para_json(detalhe.partes)
    if novas_partes:
        processo.partes_cpo = novas_partes
    elif processo.partes_cpo is None:
        processo.partes_cpo = []
    processo.sem_incidentes = _upsert_flag_cpo(processo.sem_incidentes, detalhe.sem_incidentes)
    processo.sem_apensos = _upsert_flag_cpo(processo.sem_apensos, detalhe.sem_apensos)


def _upsert_flag_cpo(atual: bool | None, novo: bool) -> bool | None:
    if novo:
        return True
    if atual is None:
        return False
    return atual


async def diff_e_persistir_peticoes_diversas(
    db: AsyncSession,
    processo_id: uuid.UUID,
    brutos: list[PeticaoDiversaRaw],
) -> list[PeticaoDiversa]:
    if not brutos:
        return []

    campos_lista: list[dict] = []
    hashes: list[str] = []
    vistos: set[str] = set()
    for raw in brutos:
        campos = peticao_para_campos(raw)
        if not campos["tipo"]:
            continue
        identidade = campos["identidade_hash"]
        if identidade in vistos:
            continue
        vistos.add(identidade)
        campos_lista.append(campos)
        hashes.append(identidade)
    if not hashes:
        return []

    resultado = await db.execute(
        select(PeticaoDiversa.identidade_hash).where(
            PeticaoDiversa.processo_id == processo_id,
            PeticaoDiversa.identidade_hash.in_(hashes),
        )
    )
    existentes = set(resultado.scalars().all())
    novas: list[PeticaoDiversa] = []
    for campos in campos_lista:
        if campos["identidade_hash"] in existentes:
            continue
        peticao = PeticaoDiversa(processo_id=processo_id, **campos)
        db.add(peticao)
        novas.append(peticao)
        existentes.add(campos["identidade_hash"])
    return novas


async def diff_e_persistir_audiencias_cpo(
    db: AsyncSession,
    processo_id: uuid.UUID,
    brutos: list[AudienciaCpoRaw],
) -> list[AudienciaCpo]:
    if not brutos:
        return []

    campos_lista: list[dict] = []
    hashes: list[str] = []
    vistos: set[str] = set()
    for raw in brutos:
        campos = audiencia_cpo_para_campos(raw)
        if not campos["titulo"]:
            continue
        identidade = campos["identidade_hash"]
        if identidade in vistos:
            continue
        vistos.add(identidade)
        campos_lista.append(campos)
        hashes.append(identidade)
    if not hashes:
        return []

    resultado = await db.execute(
        select(AudienciaCpo.identidade_hash).where(
            AudienciaCpo.processo_id == processo_id,
            AudienciaCpo.identidade_hash.in_(hashes),
        )
    )
    existentes = set(resultado.scalars().all())
    novas: list[AudienciaCpo] = []
    for campos in campos_lista:
        if campos["identidade_hash"] in existentes:
            continue
        audiencia = AudienciaCpo(processo_id=processo_id, **campos)
        db.add(audiencia)
        novas.append(audiencia)
        existentes.add(campos["identidade_hash"])
    return novas


def _titulo_notificacao_intimacao(intimacao: Intimacao) -> str:
    base = intimacao.titulo or "Mero expediente"
    return f"Nova intimação: {base}"[:255]


def _titulo_notificacao_audiencia(audiencia: Audiencia) -> str:
    base = audiencia.titulo or "Audiência"
    return f"Nova audiência: {base}"[:255]


def _titulo_notificacao_movimentacao(movimentacao: Movimentacao) -> str:
    base = movimentacao.titulo or "Nova movimentação"
    return f"Nova movimentação: {base}"[:255]


async def gerar_notificacoes(
    db: AsyncSession,
    user_id: uuid.UUID,
    novas_intimacoes: list[Intimacao],
    novas_audiencias: list[Audiencia],
    novas_movimentacoes: list[Movimentacao] | None = None,
) -> None:
    """Cria uma `Notification` por evento novo. Depois de emitir, marca
    `is_new=False` nas intimações/audiências/movimentações recém-persistidas
    — a notificação já foi gerada; a flag deixa de mentir para o painel.

    Mensagens em texto simples — o front sanitiza (DOMPurify) qualquer
    trecho vindo do e-SAJ antes de exibir, mas aqui não formatamos como
    HTML de propósito.
    """
    novas_movimentacoes = novas_movimentacoes or []
    for intimacao in novas_intimacoes:
        db.add(
            Notification(
                user_id=user_id,
                processo_id=intimacao.processo_id,
                tipo=NOTIFICATION_TIPO_INTIMACAO,
                titulo=_titulo_notificacao_intimacao(intimacao),
                message=intimacao.descricao or intimacao.titulo or "Nova intimação recebida.",
            )
        )
        intimacao.is_new = False
    for audiencia in novas_audiencias:
        data_formatada = audiencia.data_audiencia.isoformat() if audiencia.data_audiencia else "data a confirmar"
        local = f" em {audiencia.local}" if audiencia.local else ""
        db.add(
            Notification(
                user_id=user_id,
                processo_id=audiencia.processo_id,
                tipo=NOTIFICATION_TIPO_AUDIENCIA,
                titulo=_titulo_notificacao_audiencia(audiencia),
                message=f"Audiência marcada para {data_formatada}{local}.",
            )
        )
        audiencia.is_new = False
    for movimentacao in novas_movimentacoes:
        db.add(
            Notification(
                user_id=user_id,
                processo_id=movimentacao.processo_id,
                tipo=NOTIFICATION_TIPO_MOVIMENTACAO,
                titulo=_titulo_notificacao_movimentacao(movimentacao),
                message=movimentacao.descricao,
            )
        )
        movimentacao.is_new = False
