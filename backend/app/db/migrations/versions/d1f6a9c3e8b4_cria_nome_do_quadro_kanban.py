"""cria nome e descrição do quadro kanban

Revision ID: d1f6a9c3e8b4
Revises: c7a1d4e8b2f0
Create Date: 2026-10-06 15:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1f6a9c3e8b4"
down_revision: Union[str, None] = "c7a1d4e8b2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "kanban_boards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), server_default=sa.text("''"), nullable=False),
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
            name="escopo",
        ),
        sa.CheckConstraint(
            "char_length(title) >= 1 AND char_length(title) <= 80",
            name="title_len",
        ),
        sa.CheckConstraint("char_length(description) <= 280", name="description_len"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name=op.f("fk_kanban_boards_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_kanban_boards_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kanban_boards")),
    )
    op.create_index(
        "uq_kanban_boards_org",
        "kanban_boards",
        ["organization_id"],
        unique=True,
        postgresql_where=sa.text("organization_id IS NOT NULL"),
    )
    op.create_index(
        "uq_kanban_boards_user",
        "kanban_boards",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_kanban_boards_user", table_name="kanban_boards")
    op.drop_index("uq_kanban_boards_org", table_name="kanban_boards")
    op.drop_table("kanban_boards")
