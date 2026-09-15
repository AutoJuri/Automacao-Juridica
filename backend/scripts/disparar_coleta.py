"""Dispara um ciclo real de coleta e-SAJ para um usuário (sessão já `ativo`).

Uso (a partir de backend/):

    python -m uv run python scripts/disparar_coleta.py --email voce@email.com

Não faz parte da suíte pytest — fala com e-SAJ e com o Postgres reais.
Não imprime cookie, CPF nem id_esaj de intimação.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.db.session import SessionLocal  # noqa: E402
from app.services.coleta_esaj import executar_ciclo_usuario  # noqa: E402
from coleta_relatorio import (  # noqa: E402
    SNAPSHOT_PATH,
    buscar_usuario_por_email,
    delta_contagens,
    imprimir_delta,
    imprimir_relatorio,
    montar_relatorio,
    salvar_snapshot,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="E-mail da conta da plataforma")
    return parser.parse_args()


async def _main(email: str) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    async with SessionLocal() as db:
        user = await buscar_usuario_por_email(db, email)
        if user is None:
            print(f"Usuario nao encontrado: {email}")
            return 1

        relatorio_antes = await montar_relatorio(db, user)
        print("=== Antes do ciclo ===")
        imprimir_relatorio(relatorio_antes)

        if not relatorio_antes["sessao"]["pronta"]:
            print()
            print("Ciclo NAO disparado — sessao nao esta pronta.")
            return 2

        contagens_antes = relatorio_antes["contagens"]
        user_id = user.id

    print()
    print("Disparando executar_ciclo_usuario ...")
    await executar_ciclo_usuario(user_id)
    print("Ciclo retornou (excecoes internas ja foram logadas/engolidas).")

    async with SessionLocal() as db:
        user = await buscar_usuario_por_email(db, email)
        if user is None:
            print("Usuario desapareceu depois do ciclo.")
            return 1
        relatorio_depois = await montar_relatorio(db, user)
        print()
        print("=== Depois do ciclo ===")
        imprimir_relatorio(relatorio_depois)
        imprimir_delta(delta_contagens(contagens_antes, relatorio_depois["contagens"]))
        salvar_snapshot(user.email, relatorio_depois["contagens"])
        print()
        print(f"Snapshot salvo em {SNAPSHOT_PATH}")
        print("Rode verificar_coleta.py depois do 2o disparo para conferir o diff.")

    return 0


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(asyncio.run(_main(args.email)))
