"""cria colunas e tarefas do kanban

Revision ID: c7a1d4e8b2f0
Revises: b4e8c1a09f27
Create Date: 2026-10-03 01:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7a1d4e8b2f0"
down_revision: Union[str, None] = "b4e8c1a09f27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kanban_columns",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=40), nullable=False),
        sa.Column("position", sa.SmallInteger(), nullable=False),
        sa.Column("is_done", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(organization_id IS NOT NULL AND user_id IS NULL) OR "
            "(organization_id IS NULL AND user_id IS NOT NULL)",
            name="ck_kanban_columns_escopo",
        ),
        sa.CheckConstraint(
            "position >= 0 AND position <= 3",
            name="ck_kanban_columns_position_range",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_kanban_columns_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_kanban_columns_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kanban_columns")),
    )
    op.create_index(
        "uq_kanban_columns_org_position",
        "kanban_columns",
        ["organization_id", "position"],
        unique=True,
        postgresql_where=sa.text("organization_id IS NOT NULL"),
    )
    op.create_index(
        "uq_kanban_columns_user_position",
        "kanban_columns",
        ["user_id", "position"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    op.create_index(
        "uq_kanban_columns_org_done",
        "kanban_columns",
        ["organization_id"],
        unique=True,
        postgresql_where=sa.text("is_done AND organization_id IS NOT NULL"),
    )
    op.create_index(
        "uq_kanban_columns_user_done",
        "kanban_columns",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_done AND user_id IS NOT NULL"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("column_id", sa.UUID(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("processo_id", sa.UUID(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(description) <= 2000",
            name="ck_tasks_description_len",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_tasks_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["column_id"],
            ["kanban_columns.id"],
            name=op.f("fk_tasks_column_id_kanban_columns"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_tasks_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to"],
            ["users.id"],
            name=op.f("fk_tasks_assigned_to_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_tasks_processo_id_processos"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(
        "ix_tasks_org_column_position",
        "tasks",
        ["organization_id", "column_id", "position"],
    )
    op.create_index("ix_tasks_assigned_to", "tasks", ["assigned_to"])
    op.create_index("ix_tasks_created_by", "tasks", ["created_by"])
    op.add_column("notifications", sa.Column("task_id", sa.UUID(), nullable=True))
    op.add_column("notifications", sa.Column("organization_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_notifications_task_id_tasks"),
        "notifications",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_notifications_task_id", "notifications", ["task_id"])
    op.create_foreign_key(
        op.f("fk_notifications_organization_id_organizations"),
        "notifications",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # RESTRICT em tasks.column_id impede apagar coluna com tarefa. O trigger
    # apaga as tarefas antes das colunas, então excluir a organização não
    # esbarra nessa constraint.
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION apagar_quadro_da_organizacao()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $$
            BEGIN
                DELETE FROM tasks WHERE organization_id = OLD.id;
                DELETE FROM kanban_columns WHERE organization_id = OLD.id;
                RETURN OLD;
            END;
            $$
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE TRIGGER trg_organizations_apaga_quadro
            BEFORE DELETE ON organizations
            FOR EACH ROW
            EXECUTE FUNCTION apagar_quadro_da_organizacao()
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS trg_organizations_apaga_quadro ON organizations"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS apagar_quadro_da_organizacao()"))
    op.drop_constraint(
        op.f("fk_notifications_organization_id_organizations"),
        "notifications",
        type_="foreignkey",
    )
    op.drop_index("ix_notifications_task_id", table_name="notifications")
    op.drop_constraint(
        op.f("fk_notifications_task_id_tasks"),
        "notifications",
        type_="foreignkey",
    )
    op.drop_column("notifications", "organization_id")
    op.drop_column("notifications", "task_id")
    op.drop_index("ix_tasks_created_by", table_name="tasks")
    op.drop_index("ix_tasks_assigned_to", table_name="tasks")
    op.drop_index("ix_tasks_org_column_position", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index("uq_kanban_columns_user_done", table_name="kanban_columns")
    op.drop_index("uq_kanban_columns_org_done", table_name="kanban_columns")
    op.drop_index("uq_kanban_columns_user_position", table_name="kanban_columns")
    op.drop_index("uq_kanban_columns_org_position", table_name="kanban_columns")
    op.drop_table("kanban_columns")
