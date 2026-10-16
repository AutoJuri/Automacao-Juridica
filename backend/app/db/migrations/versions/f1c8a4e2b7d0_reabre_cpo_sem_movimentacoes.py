"""reabre a fila do CPO nos processos sem movimentação

Revision ID: f1c8a4e2b7d0
Revises: c3a19f2d7b64
Create Date: 2026-09-29 14:40:00.000000

O parser antigo tratava ficha sem `tabelaTodasMovimentacoes` como falta de
acesso e gravava `movimentacoes_synced_at`, mesmo quando o portal só
adiou as linhas para `carregarMovimentacoesAjax.do`. Zerar o carimbo
devolve esses processos ao início da fila. Quem já tem movimentação
não entra.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f1c8a4e2b7d0"
down_revision: Union[str, None] = "c3a19f2d7b64"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE processos
        SET movimentacoes_synced_at = NULL
        WHERE movimentacoes_synced_at IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM movimentacoes m WHERE m.processo_id = processos.id
          )
        """
    )


def downgrade() -> None:
    # O carimbo antigo não é recuperável. O próximo ciclo preenche de novo.
    pass
