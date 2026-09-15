"""Captura o HTML real do CPO (`cpopg/show.do`) de um processo — fixture
local para desenhar o parser de movimentações (Etapa 9 / ADR-010).

Uso (a partir de backend/):

    python -m uv run python scripts/capturar_cpo.py --email voce@email.com --cd-processo <cdProcesso>

Sem `--cd-processo`, lista os processos já persistidos com `url_cpo`
disponível (sem imprimir número CNJ nem partes) para você escolher um.

Não faz parte da suíte pytest — fala com o e-SAJ real. Salva o HTML bruto
em `scripts/esaj/results/cpo_<cd_processo>.html` (pasta já gitignorada, ver
`.gitignore` na raiz: `scripts/esaj/results/`). Esse arquivo é só para uso
local: nunca commitar, nunca colar conteúdo em issue/chat/commit — pode
conter nome de parte, número de processo e outros dados sigilosos.

Não imprime cookie, CPF nem o corpo da resposta — só status HTTP, host
final e o caminho/tamanho do arquivo salvo.
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
from app.models.processo import Processo  # noqa: E402
from app.models.tribunal import SESSION_STATUS_ATIVO, TRIBUNAL_ESAJ_TJSP, TribunalSession  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.esaj_http import (  # noqa: E402
    ESAJ_BASE_URL,
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
    buscar_html,
    montar_client,
)

# Fixture local — mesma pasta gitignorada usada pelo lab antigo
# (`scripts/esaj/results/`, ver docs/modulos/esaj-apis.md).
RESULTS_DIR = ROOT.parent / "scripts" / "esaj" / "results"
REFERER = f"{ESAJ_BASE_URL}/tarefas-adv/processos"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="E-mail da conta da plataforma")
    parser.add_argument(
        "--cd-processo",
        default=None,
        help="cdProcesso já persistido (com url_cpo). Sem isso, só lista as opções.",
    )
    return parser.parse_args()


async def _buscar_usuario(db, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower().strip()))


async def _buscar_sessao(db, user_id) -> TribunalSession | None:
    return await db.scalar(
        select(TribunalSession).where(
            TribunalSession.user_id == user_id,
            TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
        )
    )


async def _listar_processos_com_cpo(db, user_id) -> list[Processo]:
    resultado = await db.execute(
        select(Processo).where(Processo.user_id == user_id, Processo.url_cpo.is_not(None))
    )
    return list(resultado.scalars().all())


async def _main(email: str, cd_processo: str | None) -> int:
    async with SessionLocal() as db:
        user = await _buscar_usuario(db, email)
        if user is None:
            print(f"Usuario nao encontrado: {email}")
            return 1

        sessao = await _buscar_sessao(db, user.id)
        if (
            sessao is None
            or sessao.status != SESSION_STATUS_ATIVO
            or sessao.cookie_encrypted is None
            or sessao.cookie_expirado()
        ):
            print("Sessao e-SAJ nao esta 'ativo' com cookie valido — revalide na UI antes de capturar.")
            return 2

        if cd_processo is None:
            processos = await _listar_processos_com_cpo(db, user.id)
            if not processos:
                print("Nenhum processo com url_cpo persistido ainda — rode o ciclo de coleta primeiro.")
                return 3
            print(f"{len(processos)} processo(s) com url_cpo disponivel. Escolha um cd_processo:")
            for item in processos:
                print(f"  cd_processo={item.cd_processo}  classe={item.de_classe!r}")
            print()
            print("Rode de novo com --cd-processo <valor>.")
            return 0

        processo = await db.scalar(
            select(Processo).where(Processo.user_id == user.id, Processo.cd_processo == cd_processo)
        )
        if processo is None:
            print("cd_processo nao encontrado para este usuario.")
            return 4
        if not processo.url_cpo:
            print("Este processo nao tem url_cpo persistida.")
            return 4

        url_cpo = processo.url_cpo
        cookies: dict[str, str] | None = None
        try:
            cookies = json.loads(decrypt_secret(sessao.cookie_encrypted))
            async with montar_client(cookies) as client:
                try:
                    html = await buscar_html(client, url_cpo, referer=REFERER)
                except EsajSessaoInvalidaError:
                    print("Sessao invalidada pelo e-SAJ (redirecionou para login) — revalide e tente de novo.")
                    return 5
                except EsajRateLimitError:
                    print("Rate limit (429) do e-SAJ — aguarde e tente de novo mais tarde.")
                    return 6
                except EsajPortalIndisponivelError as exc:
                    print(f"Falha ao buscar o CPO: {type(exc).__name__}")
                    return 7
        finally:
            cookies = None

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        destino = RESULTS_DIR / f"cpo_{cd_processo}.html"
        destino.write_text(html, encoding="utf-8")

        print("HTML do CPO capturado com sucesso.")
        print(f"  tamanho: {len(html)} bytes")
        print(f"  salvo em: {destino}")
        print()
        print("Arquivo gitignorado (scripts/esaj/results/) — nao commitar, nao colar o conteudo.")
        return 0


if __name__ == "__main__":
    args = _parse_args()
    raise SystemExit(asyncio.run(_main(args.email, args.cd_processo)))
