"""cria processos_datajud

Revision ID: e5b3f7a2c916
Revises: d4a8c2e1f9b0
Create Date: 2026-09-06 01:40:00.000000

Etapa 9 (ADR-015): complemento somente-leitura do DataJud (CNJ), 1:1 com
`processos` — nunca sobrescreve os campos que vêm do e-SAJ.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e5b3f7a2c916"
down_revision: Union[str, None] = "d4a8c2e1f9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "processos_datajud",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=False),
        sa.Column("tribunal_alias", sa.String(length=30), nullable=False),
        sa.Column("classe_codigo", sa.String(length=20), nullable=True),
        sa.Column("classe_nome", sa.String(length=255), nullable=True),
        sa.Column("assuntos", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("orgao_julgador", sa.String(length=255), nullable=True),
        sa.Column("data_ajuizamento", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grau", sa.String(length=10), nullable=True),
        sa.Column("formato", sa.String(length=50), nullable=True),
        sa.Column("movimentos", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("encontrado", sa.Boolean(), nullable=False),
        sa.Column("ultima_consulta_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_processos_datajud_processo_id_processos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processos_datajud")),
    )
    # Índice único (não UniqueConstraint separada) — mesmo padrão que
    # `mapped_column(unique=True, index=True)` gera no model.
    op.create_index(
        op.f("ix_processos_datajud_processo_id"),
        "processos_datajud",
        ["processo_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_processos_datajud_processo_id"), table_name="processos_datajud")
    op.drop_table("processos_datajud")
