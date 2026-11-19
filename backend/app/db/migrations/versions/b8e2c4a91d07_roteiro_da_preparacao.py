"""roteiro cifrado da preparação da peça

Revision ID: b8e2c4a91d07
Revises: c4b8e1d7a903
Create Date: 2026-10-28 16:40:00.000000

O advogado confirma resumo, tese, pedidos e jurisprudência antes da
minuta. O JSON fica cifrado. Não guarda URL nem PDF.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b8e2c4a91d07"
down_revision: Union[str, None] = "c4b8e1d7a903"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processo_dossies",
        sa.Column("roteiro_encrypted", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("processo_dossies", "roteiro_encrypted")
