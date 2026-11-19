"""lista cifrada das peças da pasta digital

Revision ID: c4b8e1d7a903
Revises: a7d3c1e9b5f2
Create Date: 2026-10-21 16:40:00.000000

A leitura passa a entrar pela pasta (o link de Baixar PDFs). O JSON
cifrado guarda título, status e ficha. Não guarda URL nem PDF.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c4b8e1d7a903"
down_revision: Union[str, None] = "a7d3c1e9b5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processo_dossies",
        sa.Column("pecas_encrypted", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("processo_dossies", "pecas_encrypted")
