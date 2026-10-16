"""cria as pastas do drive

Revision ID: b4d8f1a6c3e2
Revises: a9c4e2b7d1f6
Create Date: 2026-10-13 18:10:00.000000

Só a pasta fica no banco. O arquivo, quando existir, mora no Google Drive
da pessoa (ADR-022). Apagar o processo solta o vínculo e mantém a pasta.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4d8f1a6c3e2"
down_revision: Union[str, None] = "a9c4e2b7d1f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drive_pastas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=True),
        sa.Column("nome", sa.String(length=120), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_drive_pastas_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name="fk_drive_pastas_processo_id_processos",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_drive_pastas"),
    )
    op.create_index(
        "ix_drive_pastas_user_id_updated_at",
        "drive_pastas",
        ["user_id", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_drive_pastas_user_id_updated_at", table_name="drive_pastas")
    op.drop_table("drive_pastas")
