"""adiciona tem_documento e url_documento em movimentacoes

Revision ID: c8f21a04b9d3
Revises: 203b0274458c
Create Date: 2026-08-24 15:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8f21a04b9d3"
down_revision: Union[str, None] = "203b0274458c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "movimentacoes",
        sa.Column("tem_documento", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("movimentacoes", sa.Column("url_documento", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("movimentacoes", "url_documento")
    op.drop_column("movimentacoes", "tem_documento")
