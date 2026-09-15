"""Mostra o estado sanitizado da coleta e-SAJ (sem disparar o ciclo).

Uso (a partir de backend/):

    python -m uv run python scripts/verificar_coleta.py --email voce@email.com

Com `--comparar`, mostra o delta em relação ao último `disparar_coleta.py`.

Não imprime cookie, CPF nem id_esaj de intimação.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal  # noqa: E402
from coleta_relatorio import (  # noqa: E402
    SNAPSHOT_PATH,
    buscar_usuario_por_email,
    carregar_snapshot,
    delta_contagens,
    imprimir_delta,
    imprimir_relatorio,
    montar_relatorio,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="E-mail da conta da plataforma")
    parser.add_argument(
        "--comparar",
        action="store_true",
        help="Compara as contagens com o snapshot do último disparar_coleta.py",
    )
    return parser.parse_args()


async def _main(email: str, comparar: bool) -> int:
    async with SessionLocal() as db:
        user = await buscar_usuario_por_email(db, email)
        if user is None:
            print(f"Usuario nao encontrado: {email}")
            return 1
        relatorio = await montar_relatorio(db, user)
        imprimir_relatorio(relatorio)

        if comparar:
            snapshot = carregar_snapshot()
            if snapshot is None:
                print()
                print(f"Nenhum snapshot em {SNAPSHOT_PATH} — rode disparar_coleta.py primeiro.")
                return 3
            if snapshot.get("email") != user.email:
                print()
                print(
                    f"Snapshot e de outro usuario ({snapshot.get('email')}) — "
                    "rode disparar_coleta.py de novo com este e-mail."
                )
                return 3
            imprimir_delta(delta_contagens(snapshot["contagens"], relatorio["contagens"]))
            print(f"(snapshot de {snapshot.get('capturado_em')})")

    return 0


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(asyncio.run(_main(args.email, args.comparar)))
