"""indice composto user_id + movimentacoes_synced_at em processos

Revision ID: b7e4c9a1d2f0
Revises: a1c0e5c0b013
Create Date: 2026-08-26 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e4c9a1d2f0"
down_revision: Union[str, None] = "a1c0e5c0b013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_processos_user_id_movimentacoes_synced_at",
        "processos",
        ["user_id", "movimentacoes_synced_at"],
        unique=False,
        postgresql_where=sa.text("url_cpo IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_processos_user_id_movimentacoes_synced_at",
        table_name="processos",
    )
