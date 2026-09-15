"""adiciona fixado em processos

Revision ID: d4a8c2e1f9b0
Revises: b7e4c9a1d2f0
Create Date: 2026-08-28 14:10:00.000000

Head do schema: precisa ir no mesmo deploy que `Processo.fixado`
(model + PATCH /processos/{id}). Sem esta revisão o Alembic não cria a
coluna e a home com pin quebra.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4a8c2e1f9b0"
down_revision: Union[str, None] = "b7e4c9a1d2f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processos",
        sa.Column(
            "fixado",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("processos", "fixado")
