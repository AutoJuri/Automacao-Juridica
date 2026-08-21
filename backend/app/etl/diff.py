"""Diff contra o banco e geração de notificações para os pipes de coleta.

`selecionar_novas_*` são funções puras (testáveis sem banco). O restante
faz I/O via SQLAlchemy — upsert de `Processo` e insert append-only de
`Intimacao`/`Audiencia`, seguido da criação das `Notification`
correspondentes só para o que é de fato novo.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.etl.etl import audiencia_para_campos, intimacao_para_campos, montar_id_esaj_audiencia, parse_datetime_esaj, processo_para_campos
from app.models.audiencia import Audiencia
from app.models.intimacao import Intimacao
from app.models.notification import NOTIFICATION_TIPO_AUDIENCIA, NOTIFICATION_TIPO_INTIMACAO, Notification
from app.models.processo import Processo
from app.models.tribunal import TRIBUNAL_ESAJ_TJSP
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


def _titulo_notificacao_intimacao(intimacao: Intimacao) -> str:
    base = intimacao.titulo or "Mero expediente"
    return f"Nova intimação: {base}"[:255]


def _titulo_notificacao_audiencia(audiencia: Audiencia) -> str:
    base = audiencia.titulo or "Audiência"
    return f"Nova audiência: {base}"[:255]


async def gerar_notificacoes(
    db: AsyncSession,
    user_id: uuid.UUID,
    novas_intimacoes: list[Intimacao],
    novas_audiencias: list[Audiencia],
) -> None:
    """Cria uma `Notification` por evento novo. Depois de emitir, marca
    `is_new=False` nas intimações/audiências recém-persistidas — a
    notificação já foi gerada; a flag deixa de mentir para o painel.

    Mensagens em texto simples — o front sanitiza (DOMPurify) qualquer
    trecho vindo do e-SAJ antes de exibir, mas aqui não formatamos como
    HTML de propósito.
    """
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
