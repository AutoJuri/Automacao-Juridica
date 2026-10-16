"""Matriz de tarefas e prazo vencido — sem banco."""

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from app.core.permissions import (
    filtro_visibilidade_tarefas,
    pode_editar_ou_mover_tarefa,
    pode_excluir_tarefa,
    ve_todas_as_tarefas,
)
from app.models.organization import (
    ROLE_ADMIN,
    ROLE_ADVOGADO,
    ROLE_ASSISTENTE,
    ROLE_ESTAGIARIO,
    ROLE_OWNER,
    OrganizationMember,
)
from app.services.tasks import tarefa_atrasada

HOJE = date(2026, 10, 3)


def _membro(papel: str) -> OrganizationMember:
    return OrganizationMember(
        organization_id=uuid4(),
        user_id=uuid4(),
        role=papel,
        joined_at=datetime.now(UTC),
    )


class TestPodeMover:
    def test_owner_e_admin_movem_tarefa_alheia(self):
        autor = uuid4()
        for papel in (ROLE_OWNER, ROLE_ADMIN):
            assert pode_editar_ou_mover_tarefa(
                papel, created_by=autor, assigned_to=autor, user_id=uuid4()
            )

    def test_advogado_so_move_se_criou_ou_recebeu(self):
        eu = uuid4()
        outro = uuid4()
        assert pode_editar_ou_mover_tarefa(
            ROLE_ADVOGADO, created_by=eu, assigned_to=outro, user_id=eu
        )
        assert pode_editar_ou_mover_tarefa(
            ROLE_ADVOGADO, created_by=outro, assigned_to=eu, user_id=eu
        )
        assert not pode_editar_ou_mover_tarefa(
            ROLE_ASSISTENTE, created_by=outro, assigned_to=outro, user_id=eu
        )


class TestPodeExcluir:
    def test_responsavel_que_nao_criou_nao_exclui(self):
        eu = uuid4()
        assert not pode_excluir_tarefa(ROLE_ADVOGADO, created_by=uuid4(), user_id=eu)
        assert pode_excluir_tarefa(ROLE_ADVOGADO, created_by=eu, user_id=eu)

    def test_owner_e_admin_excluem_qualquer(self):
        for papel in (ROLE_OWNER, ROLE_ADMIN):
            assert pode_excluir_tarefa(papel, created_by=uuid4(), user_id=uuid4())
        assert not pode_excluir_tarefa(ROLE_ASSISTENTE, created_by=uuid4(), user_id=uuid4())


class TestVisibilidade:
    def test_so_owner_e_admin_veem_todas(self):
        assert ve_todas_as_tarefas(ROLE_OWNER)
        assert ve_todas_as_tarefas(ROLE_ADMIN)
        assert not ve_todas_as_tarefas(ROLE_ADVOGADO)
        assert not ve_todas_as_tarefas(ROLE_ASSISTENTE)
        assert not ve_todas_as_tarefas(ROLE_ESTAGIARIO)

    def test_filtro_do_advogado_restringe_autor_ou_responsavel(self):
        clausula = str(
            filtro_visibilidade_tarefas(_membro(ROLE_ADVOGADO)).compile(
                dialect=postgresql.dialect()
            )
        )
        assert "organization_id" in clausula
        assert "created_by" in clausula
        assert "assigned_to" in clausula

    def test_filtro_do_owner_fica_so_na_organizacao(self):
        clausula = str(
            filtro_visibilidade_tarefas(_membro(ROLE_OWNER)).compile(
                dialect=postgresql.dialect()
            )
        )
        assert "organization_id" in clausula
        assert "created_by" not in clausula
        assert "assigned_to" not in clausula


class TestAtraso:
    def test_vencida_antes_de_hoje_e_sem_conclusao(self):
        assert tarefa_atrasada(date(2026, 10, 2), None, HOJE)
        assert not tarefa_atrasada(HOJE, None, HOJE)
        assert not tarefa_atrasada(None, None, HOJE)
        assert not tarefa_atrasada(date(2026, 10, 2), datetime.now(UTC), HOJE)
