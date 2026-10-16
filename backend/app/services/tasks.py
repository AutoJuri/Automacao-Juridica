"""Quadro de tarefas pessoal e de organização.

As duas queries não se misturam: pessoal filtra `organization_id IS NULL` e
`created_by`; organização filtra o `organization_id` do path e, para advogado,
assistente e estagiário, autor ou responsável. O papel vem do banco, nunca do JWT.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import (
    filtro_visibilidade_tarefas,
    papel_autorizado,
    pode_editar_ou_mover_tarefa,
    pode_excluir_tarefa,
)
from app.models.notification import (
    NOTIFICATION_TIPO_TASK_ATRIBUIDA,
    NOTIFICATION_TIPO_TASK_CONCLUIDA,
    Notification,
)
from app.models.organization import Organization, OrganizationMember
from app.models.processo import Processo
from app.models.task import (
    COLUNAS_PADRAO,
    DESCRICAO_QUADRO_ORG,
    DESCRICAO_QUADRO_PESSOAL,
    MAX_COLUNAS,
    TITULO_QUADRO_PADRAO,
    KanbanBoard,
    KanbanColumn,
    Task,
)
from app.models.user import User
from app.schemas.task import (
    AssigneePublicSchema,
    BoardSchema,
    ColumnPublicSchema,
    CreatorPublicSchema,
    ProcessoRefSchema,
    TaskPageSchema,
    TaskPublicSchema,
    TaskUpdateSchema,
)

FUSO_SAO_PAULO = ZoneInfo("America/Sao_Paulo")
LIMITE_TAREFAS_CONCLUSAO = 10


@dataclass(frozen=True)
class EscopoQuadro:
    user_id: UUID
    organization_id: UUID | None


def escopo_pessoal(user_id: UUID) -> EscopoQuadro:
    return EscopoQuadro(user_id=user_id, organization_id=None)


def escopo_da_org(member: OrganizationMember) -> EscopoQuadro:
    return EscopoQuadro(user_id=member.user_id, organization_id=member.organization_id)


def hoje_em_sao_paulo(agora: datetime | None = None) -> date:
    momento = agora or datetime.now(FUSO_SAO_PAULO)
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=FUSO_SAO_PAULO)
    return momento.astimezone(FUSO_SAO_PAULO).date()


def tarefa_atrasada(
    due_date: date | None,
    completed_at: datetime | None,
    hoje: date,
) -> bool:
    if due_date is None or completed_at is not None:
        return False
    return due_date < hoje


def _proibido() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sem permissão para esta ação",
    )


def _nao_encontrado(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _conflito(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _papel(member: OrganizationMember | None) -> str | None:
    return None if member is None else member.role


def _exigir_configurar(member: OrganizationMember | None) -> None:
    papel = _papel(member)
    if papel is None:
        return
    if not papel_autorizado(papel, "configurar_colunas"):
        raise _proibido()


def _exigir_mover(member: OrganizationMember | None, task: Task, user_id: UUID) -> None:
    papel = _papel(member)
    if papel is None:
        return
    if not pode_editar_ou_mover_tarefa(
        papel,
        created_by=task.created_by,
        assigned_to=task.assigned_to,
        user_id=user_id,
    ):
        raise _proibido()


def _exigir_excluir(member: OrganizationMember | None, task: Task, user_id: UUID) -> None:
    papel = _papel(member)
    if papel is None:
        return
    if not pode_excluir_tarefa(papel, created_by=task.created_by, user_id=user_id):
        raise _proibido()


async def obter_board(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
) -> BoardSchema:
    colunas = await _garantir_colunas(db, escopo)
    tarefas, contagens = await _tarefas_do_quadro(db, escopo, member, colunas)
    titulo, descricao = await _apresentacao(db, escopo)
    quadro = await _quadro_publico(
        db, colunas, tarefas, contagens, escopo.organization_id, titulo, descricao
    )
    await _commit(db)
    return quadro


async def atualizar_apresentacao(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    title: str,
    description: str,
) -> BoardSchema:
    _exigir_configurar(member)
    linha = await _buscar_quadro(db, escopo)
    if linha is None:
        linha = KanbanBoard(
            organization_id=escopo.organization_id,
            user_id=None if escopo.organization_id is not None else escopo.user_id,
            title=title,
            description=description,
        )
        db.add(linha)
    else:
        linha.title = title
        linha.description = description
    await _commit(db)
    return await obter_board(db, escopo, member)


async def criar_coluna(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    title: str,
) -> ColumnPublicSchema:
    _exigir_configurar(member)
    colunas = await _garantir_colunas(db, escopo)
    if len(colunas) >= MAX_COLUNAS:
        raise _conflito("O quadro aceita no máximo 4 colunas")
    coluna = KanbanColumn(
        organization_id=escopo.organization_id,
        user_id=None if escopo.organization_id is not None else escopo.user_id,
        title=title,
        position=len(colunas),
        is_done=False,
    )
    db.add(coluna)
    await db.flush()
    await _commit(db)
    return _coluna_publica(coluna, 0)


async def atualizar_coluna(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    column_id: UUID,
    *,
    title: str | None,
    is_done: bool | None,
    campos: set[str],
) -> ColumnPublicSchema:
    _exigir_configurar(member)
    await _travar(db, escopo)
    coluna = await _coluna_no_quadro(db, escopo, column_id)
    if "title" in campos:
        if not title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Informe o nome da coluna",
            )
        coluna.title = title
    if "is_done" in campos and is_done is not None and is_done != coluna.is_done:
        if is_done:
            for outra in await _colunas(db, escopo):
                if outra.is_done and outra.id != coluna.id:
                    outra.is_done = False
                    await _limpar_conclusao(db, outra.id)
            await db.flush()
            coluna.is_done = True
        else:
            coluna.is_done = False
            await _limpar_conclusao(db, coluna.id)
    await db.flush()
    await _commit(db)
    total = await _contar_tarefas(db, escopo, member, coluna.id)
    return _coluna_publica(coluna, total)


async def remover_coluna(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    column_id: UUID,
) -> None:
    _exigir_configurar(member)
    await _travar(db, escopo)
    coluna = await _coluna_no_quadro(db, escopo, column_id)
    atuais = await _colunas(db, escopo)
    if len(atuais) <= 1:
        raise _conflito("Não é possível remover a última coluna")
    ocupadas = await db.scalar(
        select(func.count()).select_from(Task).where(Task.column_id == coluna.id)
    )
    if ocupadas:
        raise _conflito("Remova as tarefas antes de excluir a coluna")
    await db.delete(coluna)
    await db.flush()
    restantes = [item for item in atuais if item.id != coluna.id]
    for indice, item in enumerate(restantes):
        if item.position != indice:
            item.position = indice
            await db.flush()
    await _commit(db)


async def criar_tarefa(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    *,
    title: str,
    description: str,
    column_id: UUID,
    due_date: date | None,
    processo_id: UUID | None,
    assigned_to_member_id: UUID | None,
    autor_id: UUID,
) -> TaskPublicSchema:
    await _garantir_colunas(db, escopo)
    coluna = await _coluna_no_quadro(db, escopo, column_id)
    assigned = await _responsavel(db, escopo, assigned_to_member_id, autor_id)
    if processo_id is not None:
        await _processo_do_usuario(db, autor_id, processo_id)
    total = await db.scalar(
        select(func.count()).select_from(Task).where(Task.column_id == coluna.id)
    )
    agora = datetime.now(timezone.utc)
    task = Task(
        organization_id=escopo.organization_id,
        column_id=coluna.id,
        position=int(total or 0),
        title=title,
        description=description,
        created_by=autor_id,
        assigned_to=assigned,
        processo_id=processo_id,
        due_date=due_date,
        completed_at=agora if coluna.is_done else None,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    if assigned != autor_id:
        _avisar_atribuicao(db, task, assigned)
    publica = (await _tarefas_publicas(db, [task], escopo.organization_id))[0]
    await _commit(db)
    return publica


async def atualizar_tarefa(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    task_id: UUID,
    dados: TaskUpdateSchema,
    autor_id: UUID,
) -> TaskPublicSchema:
    await _travar(db, escopo)
    task = await _tarefa_no_quadro(db, escopo, member, task_id)
    _exigir_mover(member, task, autor_id)
    campos = dados.model_fields_set
    if "title" in campos:
        if not dados.title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Informe o título da tarefa",
            )
        task.title = dados.title
    if "description" in campos:
        task.description = dados.description or ""
    if "due_date" in campos:
        task.due_date = dados.due_date
    if "processo_id" in campos:
        if dados.processo_id is None:
            task.processo_id = None
        else:
            await _processo_do_usuario(db, autor_id, dados.processo_id)
            task.processo_id = dados.processo_id
    membro_id = getattr(dados, "assigned_to_member_id", None)
    if member is not None and "assigned_to_member_id" in campos:
        if membro_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Escolha quem vai fazer a tarefa",
            )
        novo = await _responsavel(db, escopo, membro_id, autor_id)
        if novo != task.assigned_to:
            task.assigned_to = novo
            if novo != autor_id:
                _avisar_atribuicao(db, task, novo)
    await db.flush()
    await db.refresh(task)
    publica = (await _tarefas_publicas(db, [task], escopo.organization_id))[0]
    await _commit(db)
    return publica


async def mover_tarefa(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    task_id: UUID,
    column_id: UUID,
    position: int,
    autor_id: UUID,
) -> TaskPublicSchema:
    await _travar(db, escopo)
    task = await _tarefa_no_quadro(db, escopo, member, task_id)
    _exigir_mover(member, task, autor_id)
    destino = await _coluna_no_quadro(db, escopo, column_id)
    origem = await db.get(KanbanColumn, task.column_id)
    era_concluida = bool(origem is not None and origem.is_done)
    await _reordenar(db, task, destino, position)
    if destino.is_done and not era_concluida:
        task.completed_at = datetime.now(timezone.utc)
        if task.created_by != task.assigned_to and task.created_by != autor_id:
            _avisar_conclusao(db, task)
    elif not destino.is_done and era_concluida:
        task.completed_at = None
    await db.flush()
    await db.refresh(task)
    publica = (await _tarefas_publicas(db, [task], escopo.organization_id))[0]
    await _commit(db)
    return publica


async def excluir_tarefa(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    task_id: UUID,
    autor_id: UUID,
) -> None:
    await _travar(db, escopo)
    task = await _tarefa_no_quadro(db, escopo, member, task_id)
    _exigir_excluir(member, task, autor_id)
    coluna_id = task.column_id
    await db.delete(task)
    await db.flush()
    await _compactar_tarefas(db, coluna_id)
    await _commit(db)


async def _garantir_colunas(db: AsyncSession, escopo: EscopoQuadro) -> list[KanbanColumn]:
    await _travar(db, escopo)
    atuais = await _colunas(db, escopo)
    if atuais:
        return atuais
    criadas: list[KanbanColumn] = []
    for posicao, (titulo, concluida) in enumerate(COLUNAS_PADRAO):
        coluna = KanbanColumn(
            organization_id=escopo.organization_id,
            user_id=None if escopo.organization_id is not None else escopo.user_id,
            title=titulo,
            position=posicao,
            is_done=concluida,
        )
        db.add(coluna)
        criadas.append(coluna)
    await db.flush()
    return criadas


async def _travar(db: AsyncSession, escopo: EscopoQuadro) -> None:
    if escopo.organization_id is not None:
        await db.execute(
            select(Organization.id)
            .where(Organization.id == escopo.organization_id)
            .with_for_update()
        )
        return
    await db.execute(select(User.id).where(User.id == escopo.user_id).with_for_update())


async def _colunas(db: AsyncSession, escopo: EscopoQuadro) -> list[KanbanColumn]:
    stmt = select(KanbanColumn).where(*_filtro_colunas(escopo)).order_by(KanbanColumn.position)
    return list((await db.scalars(stmt)).all())


def _filtro_colunas(escopo: EscopoQuadro) -> tuple:
    if escopo.organization_id is not None:
        return (KanbanColumn.organization_id == escopo.organization_id,)
    return (
        KanbanColumn.organization_id.is_(None),
        KanbanColumn.user_id == escopo.user_id,
    )


async def _coluna_no_quadro(
    db: AsyncSession,
    escopo: EscopoQuadro,
    column_id: UUID,
) -> KanbanColumn:
    coluna = await db.scalar(
        select(KanbanColumn).where(KanbanColumn.id == column_id, *_filtro_colunas(escopo))
    )
    if coluna is None:
        raise _nao_encontrado("Coluna não encontrada")
    return coluna


async def _tarefa_no_quadro(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    task_id: UUID,
) -> Task:
    """Quem não enxerga a tarefa recebe o mesmo 404 de quem pede um id inexistente."""
    task = await db.scalar(
        select(Task).where(Task.id == task_id, _filtro_tarefas(escopo, member))
    )
    if task is None:
        raise _nao_encontrado("Tarefa não encontrada")
    return task


def _filtro_tarefas(escopo: EscopoQuadro, member: OrganizationMember | None):
    if member is None:
        return and_(Task.organization_id.is_(None), Task.created_by == escopo.user_id)
    return filtro_visibilidade_tarefas(member)


async def _tarefas_do_quadro(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    colunas: list[KanbanColumn],
) -> tuple[list[Task], dict[UUID, int]]:
    """Colunas abertas vêm inteiras. A de conclusão traz só as dez primeiras."""
    filtro = _filtro_tarefas(escopo, member)
    contagens = {coluna.id: 0 for coluna in colunas}
    conclusao = next((coluna for coluna in colunas if coluna.is_done), None)
    if conclusao is None:
        tarefas = await _buscar_ordenadas(db, filtro)
        for tarefa in tarefas:
            contagens[tarefa.column_id] = contagens.get(tarefa.column_id, 0) + 1
        return tarefas, contagens

    outras = await _buscar_ordenadas(db, and_(filtro, Task.column_id != conclusao.id))
    for tarefa in outras:
        contagens[tarefa.column_id] = contagens.get(tarefa.column_id, 0) + 1
    total = await _contar_tarefas(db, escopo, member, conclusao.id)
    contagens[conclusao.id] = total
    pagina = list(
        (
            await db.scalars(
                select(Task)
                .where(and_(filtro, Task.column_id == conclusao.id))
                .order_by(Task.position, Task.created_at)
                .limit(LIMITE_TAREFAS_CONCLUSAO)
            )
        ).all()
    )
    return outras + pagina, contagens


async def listar_pagina_conclusao(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    column_id: UUID,
    offset: int,
) -> TaskPageSchema:
    coluna = await _coluna_no_quadro(db, escopo, column_id)
    if not coluna.is_done:
        raise _nao_encontrado("Coluna não encontrada")
    filtro = and_(_filtro_tarefas(escopo, member), Task.column_id == coluna.id)
    total = await _contar_tarefas(db, escopo, member, coluna.id)
    tarefas = list(
        (
            await db.scalars(
                select(Task)
                .where(filtro)
                .order_by(Task.position, Task.created_at)
                .offset(offset)
                .limit(LIMITE_TAREFAS_CONCLUSAO)
            )
        ).all()
    )
    return TaskPageSchema(
        tasks=await _tarefas_publicas(db, tarefas, escopo.organization_id),
        total=total,
    )


async def _contar_tarefas(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member: OrganizationMember | None,
    column_id: UUID,
) -> int:
    total = await db.scalar(
        select(func.count())
        .select_from(Task)
        .where(and_(_filtro_tarefas(escopo, member), Task.column_id == column_id))
    )
    return int(total or 0)


async def _buscar_ordenadas(db: AsyncSession, filtro) -> list[Task]:
    stmt = (
        select(Task)
        .join(KanbanColumn, KanbanColumn.id == Task.column_id)
        .where(filtro)
        .order_by(KanbanColumn.position, Task.position, Task.created_at)
    )
    return list((await db.scalars(stmt)).unique().all())


async def _responsavel(
    db: AsyncSession,
    escopo: EscopoQuadro,
    member_id: UUID | None,
    autor_id: UUID,
) -> UUID:
    if escopo.organization_id is None:
        return autor_id
    if member_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Escolha quem vai fazer a tarefa",
        )
    membro = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.id == member_id,
            OrganizationMember.organization_id == escopo.organization_id,
        )
    )
    if membro is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não é membro desta organização",
        )
    return membro.user_id


async def _processo_do_usuario(db: AsyncSession, user_id: UUID, processo_id: UUID) -> None:
    existe = await db.scalar(
        select(Processo.id).where(Processo.id == processo_id, Processo.user_id == user_id)
    )
    if existe is None:
        raise _nao_encontrado("Processo não encontrado")


async def _reordenar(db: AsyncSession, task: Task, destino: KanbanColumn, position: int) -> None:
    origem_id = task.column_id
    linhas = list(
        (
            await db.scalars(
                select(Task)
                .where(Task.column_id.in_((origem_id, destino.id)))
                .order_by(Task.position, Task.created_at)
                .with_for_update()
            )
        ).all()
    )
    if origem_id == destino.id:
        lista = [item for item in linhas if item.id != task.id]
        lista.insert(_indice(position, len(lista)), task)
        for indice, item in enumerate(lista):
            item.position = indice
            item.column_id = destino.id
        return
    origem = [item for item in linhas if item.column_id == origem_id and item.id != task.id]
    destinos = [item for item in linhas if item.column_id == destino.id and item.id != task.id]
    destinos.insert(_indice(position, len(destinos)), task)
    for indice, item in enumerate(origem):
        item.position = indice
    for indice, item in enumerate(destinos):
        item.position = indice
        item.column_id = destino.id


def _indice(position: int, tamanho: int) -> int:
    return max(0, min(position, tamanho))


async def _compactar_tarefas(db: AsyncSession, column_id: UUID) -> None:
    linhas = list(
        (
            await db.scalars(
                select(Task).where(Task.column_id == column_id).order_by(Task.position, Task.created_at)
            )
        ).all()
    )
    for indice, item in enumerate(linhas):
        item.position = indice


async def _limpar_conclusao(db: AsyncSession, column_id: UUID) -> None:
    await db.execute(update(Task).where(Task.column_id == column_id).values(completed_at=None))


def _avisar_atribuicao(db: AsyncSession, task: Task, destinatario: UUID) -> None:
    db.add(
        Notification(
            user_id=destinatario,
            task_id=task.id,
            organization_id=task.organization_id,
            tipo=NOTIFICATION_TIPO_TASK_ATRIBUIDA,
            titulo="Tarefa atribuída a você",
            message=task.title,
        )
    )


def _avisar_conclusao(db: AsyncSession, task: Task) -> None:
    db.add(
        Notification(
            user_id=task.created_by,
            task_id=task.id,
            organization_id=task.organization_id,
            tipo=NOTIFICATION_TIPO_TASK_CONCLUIDA,
            titulo="Tarefa concluída",
            message=task.title,
        )
    )


async def _quadro_publico(
    db: AsyncSession,
    colunas: list[KanbanColumn],
    tarefas: list[Task],
    contagens: dict[UUID, int],
    organization_id: UUID | None,
    title: str,
    description: str,
) -> BoardSchema:
    return BoardSchema(
        title=title,
        description=description,
        columns=[_coluna_publica(coluna, contagens.get(coluna.id, 0)) for coluna in colunas],
        tasks=await _tarefas_publicas(db, tarefas, organization_id),
    )


def _descricao_padrao(escopo: EscopoQuadro) -> str:
    if escopo.organization_id is not None:
        return DESCRICAO_QUADRO_ORG
    return DESCRICAO_QUADRO_PESSOAL


async def _buscar_quadro(db: AsyncSession, escopo: EscopoQuadro) -> KanbanBoard | None:
    if escopo.organization_id is not None:
        filtro = KanbanBoard.organization_id == escopo.organization_id
    else:
        filtro = and_(
            KanbanBoard.user_id == escopo.user_id,
            KanbanBoard.organization_id.is_(None),
        )
    return await db.scalar(select(KanbanBoard).where(filtro))


async def _apresentacao(db: AsyncSession, escopo: EscopoQuadro) -> tuple[str, str]:
    linha = await _buscar_quadro(db, escopo)
    if linha is None:
        return TITULO_QUADRO_PADRAO, _descricao_padrao(escopo)
    return linha.title, linha.description


def _coluna_publica(coluna: KanbanColumn, task_count: int) -> ColumnPublicSchema:
    return ColumnPublicSchema(
        id=coluna.id,
        title=coluna.title,
        position=coluna.position,
        is_done=coluna.is_done,
        task_count=task_count,
    )


async def _tarefas_publicas(
    db: AsyncSession,
    tarefas: list[Task],
    organization_id: UUID | None,
) -> list[TaskPublicSchema]:
    if not tarefas:
        return []
    user_ids = {task.created_by for task in tarefas}
    user_ids.update(task.assigned_to for task in tarefas if task.assigned_to is not None)
    usuarios = {
        usuario.id: usuario
        for usuario in (
            await db.scalars(select(User).where(User.id.in_(user_ids)))
        ).all()
    }
    membros: dict[UUID, OrganizationMember] = {}
    if organization_id is not None:
        linhas = (
            await db.scalars(
                select(OrganizationMember).where(
                    OrganizationMember.organization_id == organization_id,
                    OrganizationMember.user_id.in_(user_ids),
                )
            )
        ).all()
        membros = {membro.user_id: membro for membro in linhas}
    processo_ids = {task.processo_id for task in tarefas if task.processo_id is not None}
    numeros: dict[UUID, str | None] = {}
    if processo_ids:
        consulta = await db.execute(
            select(Processo.id, Processo.nu_processo).where(Processo.id.in_(processo_ids))
        )
        numeros = {processo_id: numero for processo_id, numero in consulta.all()}
    hoje = hoje_em_sao_paulo()
    return [
        _tarefa_publica(task, usuarios, membros, numeros, hoje)
        for task in tarefas
    ]


def _tarefa_publica(
    task: Task,
    usuarios: dict[UUID, User],
    membros: dict[UUID, OrganizationMember],
    numeros: dict[UUID, str | None],
    hoje: date,
) -> TaskPublicSchema:
    criador = usuarios.get(task.created_by)
    assignee = None
    if task.assigned_to is not None and task.assigned_to in usuarios:
        membro = membros.get(task.assigned_to)
        assignee = AssigneePublicSchema(
            member_id=None if membro is None else membro.id,
            name=usuarios[task.assigned_to].name,
        )
    processo = None
    if task.processo_id is not None and task.processo_id in numeros:
        processo = ProcessoRefSchema(id=task.processo_id, nu_processo=numeros[task.processo_id])
    return TaskPublicSchema(
        id=task.id,
        column_id=task.column_id,
        position=task.position,
        title=task.title,
        description=task.description,
        assignee=assignee,
        created_by=CreatorPublicSchema(name="" if criador is None else criador.name),
        processo=processo,
        due_date=task.due_date,
        is_overdue=tarefa_atrasada(task.due_date, task.completed_at, hoje),
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def _commit(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise _conflito("Não foi possível atualizar o quadro") from exc
