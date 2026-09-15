"""enriquece processos com capa CPO, peticoes diversas e audiencias CPO

Revision ID: a1c0e5c0b013
Revises: c8f21a04b9d3
Create Date: 2026-08-25 22:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a1c0e5c0b013"
down_revision: Union[str, None] = "c8f21a04b9d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("processos", sa.Column("foro", sa.String(length=255), nullable=True))
    op.add_column("processos", sa.Column("vara", sa.String(length=255), nullable=True))
    op.add_column("processos", sa.Column("juiz", sa.String(length=255), nullable=True))
    op.add_column("processos", sa.Column("distribuicao", sa.String(length=255), nullable=True))
    op.add_column("processos", sa.Column("controle", sa.String(length=50), nullable=True))
    op.add_column("processos", sa.Column("area", sa.String(length=50), nullable=True))
    op.add_column("processos", sa.Column("valor_acao", sa.String(length=100), nullable=True))
    op.add_column(
        "processos",
        sa.Column("partes_cpo", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column("processos", sa.Column("sem_incidentes", sa.Boolean(), nullable=True))
    op.add_column("processos", sa.Column("sem_apensos", sa.Boolean(), nullable=True))

    op.create_table(
        "peticoes_diversas",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=False),
        sa.Column("data_peticao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tipo", sa.String(length=255), nullable=False),
        sa.Column("protocolo", sa.String(length=100), nullable=True),
        sa.Column("identidade_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_peticoes_diversas_processo_id_processos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_peticoes_diversas")),
        sa.UniqueConstraint("processo_id", "identidade_hash", name=op.f("uq_peticoes_diversas_processo_id_identidade_hash")),
    )
    op.create_index(op.f("ix_peticoes_diversas_processo_id"), "peticoes_diversas", ["processo_id"])
    op.create_index(op.f("ix_peticoes_diversas_data_peticao"), "peticoes_diversas", ["data_peticao"])

    op.create_table(
        "audiencias_cpo",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("processo_id", sa.UUID(), nullable=False),
        sa.Column("data_audiencia", sa.DateTime(timezone=True), nullable=True),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("situacao", sa.String(length=100), nullable=True),
        sa.Column("qt_pessoas", sa.String(length=20), nullable=True),
        sa.Column("identidade_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["processo_id"],
            ["processos.id"],
            name=op.f("fk_audiencias_cpo_processo_id_processos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audiencias_cpo")),
        sa.UniqueConstraint("processo_id", "identidade_hash", name=op.f("uq_audiencias_cpo_processo_id_identidade_hash")),
    )
    op.create_index(op.f("ix_audiencias_cpo_processo_id"), "audiencias_cpo", ["processo_id"])
    op.create_index(op.f("ix_audiencias_cpo_data_audiencia"), "audiencias_cpo", ["data_audiencia"])


def downgrade() -> None:
    op.drop_index(op.f("ix_audiencias_cpo_data_audiencia"), table_name="audiencias_cpo")
    op.drop_index(op.f("ix_audiencias_cpo_processo_id"), table_name="audiencias_cpo")
    op.drop_table("audiencias_cpo")
    op.drop_index(op.f("ix_peticoes_diversas_data_peticao"), table_name="peticoes_diversas")
    op.drop_index(op.f("ix_peticoes_diversas_processo_id"), table_name="peticoes_diversas")
    op.drop_table("peticoes_diversas")
    op.drop_column("processos", "sem_apensos")
    op.drop_column("processos", "sem_incidentes")
    op.drop_column("processos", "partes_cpo")
    op.drop_column("processos", "valor_acao")
    op.drop_column("processos", "area")
    op.drop_column("processos", "controle")
    op.drop_column("processos", "distribuicao")
    op.drop_column("processos", "juiz")
    op.drop_column("processos", "vara")
    op.drop_column("processos", "foro")
