"""adiciona estilo_perfil_encrypted em elaboracoes

Revision ID: c3a19f2d7b64
Revises: e782fdd01295
Create Date: 2026-09-22 23:40:00.000000

ADR-016 Fase 3 — perfil de estilo (JSON) extraído do texto de um modelo de
peça, cifrado com AES-256-GCM (mesma função de `fatos_extras_encrypted`).
Nullable: só existe depois que o advogado aplica um modelo nesta sessão.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a19f2d7b64"
down_revision: Union[str, None] = "e782fdd01295"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "elaboracoes",
        sa.Column("estilo_perfil_encrypted", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("elaboracoes", "estilo_perfil_encrypted")
