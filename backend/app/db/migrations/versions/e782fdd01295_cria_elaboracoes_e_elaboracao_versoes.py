"""acrescenta fatos extras e versões da minuta

Revision ID: e782fdd01295
Revises: c7e2a9d4b1f8
Create Date: 2026-09-21 23:41:05.978608

A capa `elaboracoes` já existe (ADR-021). Esta revisão só guarda o texto da
IA: fatos extras cifrados na capa e o histórico em `elaboracao_versoes`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e782fdd01295"
down_revision: Union[str, None] = "c7e2a9d4b1f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    colunas = {coluna["name"] for coluna in inspector.get_columns("elaboracoes")}
    if "fatos_extras_encrypted" not in colunas:
        op.add_column(
            "elaboracoes",
            sa.Column("fatos_extras_encrypted", sa.LargeBinary(), nullable=True),
        )
    if "elaboracao_versoes" in inspector.get_table_names():
        return
    op.create_table(
        "elaboracao_versoes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("elaboracao_id", sa.UUID(), nullable=False),
        sa.Column("origem", sa.String(length=20), nullable=False),
        sa.Column("instrucao_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("trecho_alvo_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("conteudo_encrypted", sa.LargeBinary(), nullable=False),
        sa.Column("llm_provider", sa.String(length=30), nullable=False),
        sa.Column("llm_model", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["elaboracao_id"],
            ["elaboracoes.id"],
            name=op.f("fk_elaboracao_versoes_elaboracao_id_elaboracoes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_elaboracao_versoes")),
    )
    op.create_index(
        op.f("ix_elaboracao_versoes_elaboracao_id"),
        "elaboracao_versoes",
        ["elaboracao_id"],
        unique=False,
    )
    op.create_index(
        "ix_elaboracao_versoes_elaboracao_id_created_at",
        "elaboracao_versoes",
        ["elaboracao_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_elaboracao_versoes_elaboracao_id_created_at", table_name="elaboracao_versoes"
    )
    op.drop_index(op.f("ix_elaboracao_versoes_elaboracao_id"), table_name="elaboracao_versoes")
    op.drop_table("elaboracao_versoes")
    op.drop_column("elaboracoes", "fatos_extras_encrypted")
