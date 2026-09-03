"""Consultas do painel: processos, intimações, audiências e notificações.

Toda query filtra `user_id` no banco. Nenhum mapper inclui `id_esaj`.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audiencia import Audiencia
from app.models.audiencia_cpo import AudienciaCpo
from app.models.intimacao import Intimacao
from app.models.movimentacao import Movimentacao
from app.models.notification import Notification
from app.models.peticao_diversa import PeticaoDiversa
from app.models.processo import Processo
from app.schemas.notification import NotificationPublicSchema
from app.schemas.processo import (
    AudienciaCpoPublicSchema,
    AudienciaPainelSchema,
    AudienciaPublicSchema,
    IntimacaoPainelSchema,
    IntimacaoPublicSchema,
    MovimentacaoPublicSchema,
    ParteCpoPublicSchema,
    PartePublicSchema,
    PeticaoDiversaPublicSchema,
    ProcessoDetalheSchema,
    ProcessoListSchema,
    UltimaAtividadeSchema,
)
from app.services.esaj_cpo_parser import url_documento_publica

LISTA_MAX = 200
NOTIFICACOES_MAX = 50


def _parte_publica(parte: dict | None) -> PartePublicSchema | None:
    if not parte:
        return None
    nome = parte.get("nome") or parte.get("nomeSocial")
    representada = parte.get("representada")
    if nome is None and representada is None:
        return None
    return PartePublicSchema(
        nome=nome if isinstance(nome, str) else None,
        representada=representada if isinstance(representada, bool) else None,
    )


def _data_intimacao(item: Intimacao) -> datetime | None:
    return item.data_movimentacao or item.created_at


def _data_audiencia(item: Audiencia) -> datetime | None:
    return item.data_audiencia or item.created_at


def montar_ultima_atividade(
    intimacoes: list[Intimacao], audiencias: list[Audiencia]
) -> UltimaAtividadeSchema | None:
    candidatos: list[tuple[str, str | None, datetime]] = []
    for item in intimacoes:
        data = _data_intimacao(item)
        if data is not None:
            candidatos.append(("intimacao", item.titulo, data))
    for item in audiencias:
        data = _data_audiencia(item)
        if data is not None:
            candidatos.append(("audiencia", item.titulo, data))
    if not candidatos:
        return None
    tipo, titulo, data = max(candidatos, key=lambda c: c[2])
    return UltimaAtividadeSchema(tipo=tipo, titulo=titulo, data=data)


def _ordenar_audiencias(audiencias: list[Audiencia]) -> list[Audiencia]:
    agora = datetime.now(UTC)
    proximas = [a for a in audiencias if a.data_audiencia is not None and a.data_audiencia >= agora]
    passadas = [a for a in audiencias if a.data_audiencia is None or a.data_audiencia < agora]
    proximas.sort(key=lambda a: a.data_audiencia or agora)
    epoch = datetime.min.replace(tzinfo=UTC)
    passadas.sort(key=lambda a: a.data_audiencia or epoch, reverse=True)
    return proximas + passadas


def processo_para_lista(
    processo: Processo,
    intimacoes: list[Intimacao],
    audiencias: list[Audiencia],
) -> ProcessoListSchema:
    return ProcessoListSchema(
        id=processo.id,
        tribunal=processo.tribunal,
        nu_processo=processo.nu_processo,
        de_classe=processo.de_classe,
        de_assunto=processo.de_assunto,
        instancia=processo.instancia,
        parte_ativa=_parte_publica(processo.parte_ativa),
        parte_passiva=_parte_publica(processo.parte_passiva),
        last_synced_at=processo.last_synced_at,
        ultima_atividade=montar_ultima_atividade(intimacoes, audiencias),
        fixado=bool(getattr(processo, "fixado", False)),
    )


def intimacao_para_publico(item: Intimacao) -> IntimacaoPublicSchema:
    return IntimacaoPublicSchema(
        id=item.id,
        titulo=item.titulo,
        descricao=item.descricao,
        instancia=item.instancia,
        data_movimentacao=item.data_movimentacao,
        ciencia=item.ciencia,
    )


def audiencia_para_publico(item: Audiencia) -> AudienciaPublicSchema:
    return AudienciaPublicSchema(
        id=item.id,
        titulo=item.titulo,
        data_audiencia=item.data_audiencia,
        local=item.local,
    )


def descricao_sem_titulo(titulo: str | None, descricao: str) -> str:
    """O parser grava a primeira linha da célula também em `titulo`, e o
    texto completo (incluindo essa linha) em `descricao`. Na API pública
    a linha do título não se repete — o hash no banco continua no texto
    original, para não recriar movimentações como se fossem novas.
    """
    if not descricao:
        return ""
    linhas = descricao.split("\n")
    if titulo and linhas and linhas[0].strip() == titulo.strip():
        return "\n".join(linhas[1:]).strip()
    return descricao


def movimentacao_para_publico(item: Movimentacao) -> MovimentacaoPublicSchema:
    return MovimentacaoPublicSchema(
        id=item.id,
        titulo=item.titulo,
        descricao=descricao_sem_titulo(item.titulo, item.descricao),
        data_movimentacao=item.data_movimentacao,
        tem_documento=bool(getattr(item, "tem_documento", False)),
        url_documento=url_documento_publica(getattr(item, "url_documento", None)),
    )


def _status_movimentacoes(
    processo: Processo, movimentacoes: list[Movimentacao]
) -> str:
    if movimentacoes:
        return "ok"
    if getattr(processo, "movimentacoes_synced_at", None) is None:
        return "pendente"
    return "indisponivel"


def _ordenar_movimentacoes(movimentacoes: list[Movimentacao]) -> list[Movimentacao]:
    epoch = datetime.min.replace(tzinfo=UTC)
    return sorted(movimentacoes, key=lambda m: m.data_movimentacao or epoch, reverse=True)


def _ordenar_por_data(itens: list, attr: str) -> list:
    epoch = datetime.min.replace(tzinfo=UTC)
    return sorted(itens, key=lambda item: getattr(item, attr) or epoch, reverse=True)


def _partes_cpo_para_publico(valor: object) -> list[ParteCpoPublicSchema]:
    if not isinstance(valor, list):
        return []
    saida: list[ParteCpoPublicSchema] = []
    for item in valor:
        if not isinstance(item, dict):
            continue
        papel = str(item.get("papel") or "").strip()
        if not papel:
            continue
        nome = str(item["nome"]).strip() if item.get("nome") else None
        advogados = str(item["advogados"]).strip() if item.get("advogados") else None
        saida.append(
            ParteCpoPublicSchema(
                papel=papel,
                nome=nome or None,
                advogados=advogados or None,
            )
        )
    return saida


def peticao_para_publico(item: PeticaoDiversa) -> PeticaoDiversaPublicSchema:
    return PeticaoDiversaPublicSchema.model_validate(item)


def audiencia_cpo_para_publico(item: AudienciaCpo) -> AudienciaCpoPublicSchema:
    return AudienciaCpoPublicSchema.model_validate(item)


def processo_para_detalhe(
    processo: Processo,
    intimacoes: list[Intimacao],
    audiencias: list[Audiencia],
    movimentacoes: list[Movimentacao] | None = None,
    peticoes: list[PeticaoDiversa] | None = None,
    audiencias_cpo: list[AudienciaCpo] | None = None,
) -> ProcessoDetalheSchema:
    lista = processo_para_lista(processo, intimacoes, audiencias)
    intimacoes_ord = sorted(
        intimacoes,
        key=lambda i: _data_intimacao(i) or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    movs = movimentacoes or []
    return ProcessoDetalheSchema(
        **lista.model_dump(),
        url_cpo=processo.url_cpo,
        url_pasta=processo.url_pasta,
        foro=getattr(processo, "foro", None),
        vara=getattr(processo, "vara", None),
        juiz=getattr(processo, "juiz", None),
        distribuicao=getattr(processo, "distribuicao", None),
        controle=getattr(processo, "controle", None),
        area=getattr(processo, "area", None),
        valor_acao=getattr(processo, "valor_acao", None),
        partes_cpo=_partes_cpo_para_publico(getattr(processo, "partes_cpo", None)),
        intimacoes=[intimacao_para_publico(i) for i in intimacoes_ord],
        audiencias=[audiencia_para_publico(a) for a in _ordenar_audiencias(audiencias)],
        movimentacoes=[movimentacao_para_publico(m) for m in _ordenar_movimentacoes(movs)],
        peticoes_diversas=[
            peticao_para_publico(p) for p in _ordenar_por_data(peticoes or [], "data_peticao")
        ],
        audiencias_cpo=[
            audiencia_cpo_para_publico(a)
            for a in _ordenar_por_data(audiencias_cpo or [], "data_audiencia")
        ],
        movimentacoes_status=_status_movimentacoes(processo, movs),
        sem_incidentes=getattr(processo, "sem_incidentes", None),
        sem_apensos=getattr(processo, "sem_apensos", None),
    )


def notificacao_para_publico(item: Notification) -> NotificationPublicSchema:
    return NotificationPublicSchema.model_validate(item)


async def listar_processos(
    db: AsyncSession, user_id: UUID, *, q: str | None = None
) -> list[ProcessoListSchema]:
    stmt = select(Processo).where(Processo.user_id == user_id)
    termo = (q or "").strip()
    if termo:
        like = f"%{termo}%"
        stmt = stmt.where(
            or_(
                Processo.nu_processo.ilike(like),
                Processo.de_classe.ilike(like),
                Processo.de_assunto.ilike(like),
                Processo.parte_ativa["nome"].astext.ilike(like),
            )
        )
    processos = list((await db.scalars(stmt.limit(LISTA_MAX))).all())
    if not processos:
        return []

    ids = [p.id for p in processos]
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

    intimacoes_por: dict[UUID, list[Intimacao]] = {p.id: [] for p in processos}
    audiencias_por: dict[UUID, list[Audiencia]] = {p.id: [] for p in processos}
    for item in intimacoes:
        if item.processo_id is not None:
            intimacoes_por.setdefault(item.processo_id, []).append(item)
    for item in audiencias:
        if item.processo_id is not None:
            audiencias_por.setdefault(item.processo_id, []).append(item)

    itens = [
        processo_para_lista(p, intimacoes_por.get(p.id, []), audiencias_por.get(p.id, []))
        for p in processos
    ]
    epoch = datetime.min.replace(tzinfo=UTC)
    itens.sort(
        key=lambda item: (
            item.fixado,
            item.ultima_atividade.data
            if item.ultima_atividade and item.ultima_atividade.data
            else epoch,
        ),
        reverse=True,
    )
    return itens


async def buscar_processo_detalhe(
    db: AsyncSession, user_id: UUID, processo_id: UUID
) -> ProcessoDetalheSchema | None:
    processo = await db.scalar(
        select(Processo).where(Processo.id == processo_id, Processo.user_id == user_id)
    )
    if processo is None:
        return None

    intimacoes = list(
        (
            await db.scalars(
                select(Intimacao).where(
                    Intimacao.user_id == user_id,
                    Intimacao.processo_id == processo_id,
                )
            )
        ).all()
    )
    audiencias = list(
        (
            await db.scalars(
                select(Audiencia).where(
                    Audiencia.user_id == user_id,
                    Audiencia.processo_id == processo_id,
                )
            )
        ).all()
    )
    movimentacoes = list(
        (
            await db.scalars(
                select(Movimentacao)
                .join(Processo, Movimentacao.processo_id == Processo.id)
                .where(Processo.id == processo_id, Processo.user_id == user_id)
            )
        ).all()
    )
    peticoes = list(
        (
            await db.scalars(
                select(PeticaoDiversa)
                .join(Processo, PeticaoDiversa.processo_id == Processo.id)
                .where(Processo.id == processo_id, Processo.user_id == user_id)
            )
        ).all()
    )
    audiencias_cpo = list(
        (
            await db.scalars(
                select(AudienciaCpo)
                .join(Processo, AudienciaCpo.processo_id == Processo.id)
                .where(Processo.id == processo_id, Processo.user_id == user_id)
            )
        ).all()
    )
    return processo_para_detalhe(
        processo, intimacoes, audiencias, movimentacoes, peticoes, audiencias_cpo
    )


async def atualizar_fixado(
    db: AsyncSession, user_id: UUID, processo_id: UUID, *, fixado: bool
) -> ProcessoListSchema | None:
    processo = await db.scalar(
        select(Processo).where(Processo.id == processo_id, Processo.user_id == user_id)
    )
    if processo is None:
        return None
    processo.fixado = fixado
    await db.commit()
    await db.refresh(processo)
    return processo_para_lista(processo, [], [])


def intimacao_para_painel(item: Intimacao, processo: Processo | None) -> IntimacaoPainelSchema:
    ficha = processo if processo is not None and processo.user_id == item.user_id else None
    return IntimacaoPainelSchema(
        id=item.id,
        processo_id=item.processo_id if ficha is not None else None,
        nu_processo=ficha.nu_processo if ficha is not None else None,
        tribunal=ficha.tribunal if ficha is not None else None,
        instancia=item.instancia or (ficha.instancia if ficha is not None else None),
        titulo=item.titulo,
        descricao=item.descricao,
        data_movimentacao=item.data_movimentacao,
        ciencia=item.ciencia,
        foro=getattr(ficha, "foro", None) if ficha is not None else None,
        vara=getattr(ficha, "vara", None) if ficha is not None else None,
    )


def audiencia_para_painel(
    *,
    item_id: UUID,
    processo: Processo | None,
    user_id: UUID,
    titulo: str,
    data_audiencia: datetime | None,
    local: str | None,
    situacao: str | None,
    fonte: Literal["agenda", "cpo"],
) -> AudienciaPainelSchema:
    ficha = processo if processo is not None and processo.user_id == user_id else None
    return AudienciaPainelSchema(
        id=item_id,
        processo_id=ficha.id if ficha is not None else None,
        nu_processo=ficha.nu_processo if ficha is not None else None,
        tribunal=ficha.tribunal if ficha is not None else None,
        titulo=titulo,
        data_audiencia=data_audiencia,
        local=local,
        situacao=situacao,
        parte_ativa=_parte_publica(ficha.parte_ativa) if ficha is not None else None,
        parte_passiva=_parte_publica(ficha.parte_passiva) if ficha is not None else None,
        foro=getattr(ficha, "foro", None) if ficha is not None else None,
        vara=getattr(ficha, "vara", None) if ficha is not None else None,
        juiz=getattr(ficha, "juiz", None) if ficha is not None else None,
        fonte=fonte,
    )


def _on_processo_do_usuario(fk_processo_id, user_id):
    """ON do join: mesmo id **e** mesmo advogado. Sem isso o SQL puxaria
    a ficha de outro usuário se `processo_id` apontasse para o processo dele.
    """
    return (fk_processo_id == Processo.id) & (Processo.user_id == user_id)


async def listar_intimacoes_painel(
    db: AsyncSession, user_id: UUID
) -> list[IntimacaoPainelSchema]:
    stmt = (
        select(Intimacao, Processo)
        .outerjoin(Processo, _on_processo_do_usuario(Intimacao.processo_id, user_id))
        .where(Intimacao.user_id == user_id)
        .order_by(Intimacao.data_movimentacao.desc())
        .limit(LISTA_MAX)
    )
    linhas = list((await db.execute(stmt)).all())
    return [intimacao_para_painel(item, processo) for item, processo in linhas]


async def listar_audiencias_painel(
    db: AsyncSession, user_id: UUID
) -> list[AudienciaPainelSchema]:
    stmt_agenda = (
        select(Audiencia, Processo)
        .outerjoin(Processo, _on_processo_do_usuario(Audiencia.processo_id, user_id))
        .where(Audiencia.user_id == user_id)
        .limit(LISTA_MAX)
    )
    agenda = list((await db.execute(stmt_agenda)).all())
    saida = [
        audiencia_para_painel(
            item_id=item.id,
            processo=processo,
            user_id=user_id,
            titulo=(item.titulo or "").strip() or "Audiência",
            data_audiencia=item.data_audiencia,
            local=item.local,
            situacao=None,
            fonte="agenda",
        )
        for item, processo in agenda
    ]

    stmt_cpo = (
        select(AudienciaCpo, Processo)
        .join(Processo, _on_processo_do_usuario(AudienciaCpo.processo_id, user_id))
        .limit(LISTA_MAX)
    )
    cpo = list((await db.execute(stmt_cpo)).all())
    saida.extend(
        audiencia_para_painel(
            item_id=item.id,
            processo=processo,
            user_id=user_id,
            titulo=(item.titulo or "").strip() or "Audiência",
            data_audiencia=item.data_audiencia,
            local=None,
            situacao=item.situacao,
            fonte="cpo",
        )
        for item, processo in cpo
    )

    epoch = datetime.min.replace(tzinfo=UTC)
    saida.sort(key=lambda item: item.data_audiencia or epoch, reverse=True)
    return saida[:LISTA_MAX]


async def listar_notificacoes(
    db: AsyncSession, user_id: UUID, *, somente_nao_lidas: bool = False
) -> list[NotificationPublicSchema]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if somente_nao_lidas:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.is_read.asc(), Notification.created_at.desc()).limit(
        NOTIFICACOES_MAX
    )
    itens = list((await db.scalars(stmt)).all())
    return [notificacao_para_publico(item) for item in itens]


async def marcar_notificacao_lida(
    db: AsyncSession, user_id: UUID, notificacao_id: UUID
) -> NotificationPublicSchema | None:
    item = await db.scalar(
        select(Notification).where(Notification.id == notificacao_id, Notification.user_id == user_id)
    )
    if item is None:
        return None
    item.is_read = True
    await db.commit()
    await db.refresh(item)
    return notificacao_para_publico(item)


async def marcar_todas_lidas(db: AsyncSession, user_id: UUID) -> int:
    resultado = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    await db.commit()
    return int(resultado.rowcount or 0)
