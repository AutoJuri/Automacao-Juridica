"""Mede o que `abrirDocumentoVinculadoMovimentacao.do` devolve com o cookie.

Uso (a partir de backend/):

    python -m uv run python scripts/sondar_documento_esaj.py --email voce@email.com --cd-processo <cdProcesso>

Não grava o PDF nem o HTML. A saída é só status, content-type, tamanho,
se redirecionou, se os bytes começam com %PDF e o path (sem query) de
um salto allowlisted. Nada de URL, número de processo, cookie ou CPF.

No máximo 3 documentos, com pausa entre eles. O corpo fica em memória
e é descartado ao fim de cada um.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.security import decrypt_secret  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.movimentacao import Movimentacao  # noqa: E402
from app.models.processo import Processo  # noqa: E402
from app.models.tribunal import SESSION_STATUS_ATIVO, TRIBUNAL_ESAJ_TJSP, TribunalSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.esaj_documentos import sondar_documento  # noqa: E402
from app.services.esaj_http import montar_client  # noqa: E402

LIMITE = 3
PAUSA_SEGUNDOS = 1.0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="E-mail da conta da plataforma")
    parser.add_argument("--cd-processo", required=True, help="cdProcesso já persistido")
    return parser.parse_args()


def _imprimir(sonda) -> None:
    print(f"  status_http={sonda.status_http if sonda.status_http is not None else '-'}")
    print(f"  content_type={sonda.content_type or '-'}")
    print(f"  tamanho={sonda.tamanho}")
    print(f"  redirecionou={'sim' if sonda.redirecionou else 'nao'}")
    print(f"  parece_pdf={'sim' if sonda.parece_pdf else 'nao'}")
    print(f"  caminho={sonda.caminho or '-'}")
    print(f"  causa={sonda.causa}")


async def _main(email: str, cd_processo: str) -> int:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email.lower().strip()))
        if user is None:
            print("Usuario nao encontrado.")
            return 1

        sessao = await db.scalar(
            select(TribunalSession).where(
                TribunalSession.user_id == user.id,
                TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
            )
        )
        if (
            sessao is None
            or sessao.status != SESSION_STATUS_ATIVO
            or sessao.cookie_encrypted is None
            or sessao.cookie_expirado()
        ):
            print("Sessao e-SAJ nao esta ativo com cookie valido.")
            return 2

        processo = await db.scalar(
            select(Processo).where(
                Processo.user_id == user.id,
                Processo.cd_processo == cd_processo,
            )
        )
        if processo is None:
            print("cd_processo nao encontrado para este usuario.")
            return 4

        movs = (
            await db.scalars(
                select(Movimentacao)
                .where(
                    Movimentacao.processo_id == processo.id,
                    Movimentacao.url_documento.is_not(None),
                )
                .limit(LIMITE)
            )
        ).all()
        urls = [mov.url_documento for mov in movs if mov.url_documento]
        if not urls:
            print("Nenhum documento com URL neste processo.")
            return 3

        cookies: dict[str, str] | None = None
        try:
            cookies = json.loads(decrypt_secret(sessao.cookie_encrypted))
            async with montar_client(cookies) as client:
                print(f"documentos={len(urls)}")
                for indice, url in enumerate(urls, start=1):
                    print(f"--- {indice}")
                    sonda = await sondar_documento(client, url)
                    _imprimir(sonda)
                    if indice < len(urls):
                        await asyncio.sleep(PAUSA_SEGUNDOS)
        finally:
            cookies = None
    return 0


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(asyncio.run(_main(args.email, args.cd_processo)))
