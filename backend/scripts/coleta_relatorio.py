"""Relatório sanitizado do estado da coleta e-SAJ (uso local / smoke).

Nunca imprime cookie, CPF, senha, token OAuth2 nem `id_esaj` de intimação
(o id da API carrega OAB). Número CNJ e títulos saem porque o teste manual
precisa cruzar com o portal — não cole a saída em issue/commit/chat público.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audiencia import Audiencia
from app.models.intimacao import Intimacao
from app.models.job_log import JobLog
from app.models.notification import Notification
from app.models.processo import Processo
from app.models.tribunal import TRIBUNAL_ESAJ_TJSP, TribunalSession
from app.models.user import User

SNAPSHOT_PATH = Path(__file__).resolve().parent / ".coleta_snapshot.json"
AMOSTRAS = 8
JOBS_RECENTES = 12


async def buscar_usuario_por_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower().strip()))


async def buscar_sessao(db: AsyncSession, user_id: UUID) -> TribunalSession | None:
    return await db.scalar(
        select(TribunalSession).where(
            TribunalSession.user_id == user_id,
            TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
        )
    )


async def contar(db: AsyncSession, user_id: UUID) -> dict[str, int]:
    async def _q(model) -> int:
        resultado = await db.scalar(select(func.count()).select_from(model).where(model.user_id == user_id))
        return int(resultado or 0)

    return {
        "processos": await _q(Processo),
        "intimacoes": await _q(Intimacao),
        "audiencias": await _q(Audiencia),
        "notifications": await _q(Notification),
    }


def sessao_pronta(sessao: TribunalSession | None) -> tuple[bool, str]:
    if sessao is None:
        return False, "Nenhuma TribunalSession — cadastre credenciais e-SAJ e conecte o e-mail."
    if sessao.status != "ativo":
        return False, (
            f"Sessão status={sessao.status!r} (precisa ser 'ativo'). "
            "Abra Configurações e clique em Revalidar."
        )
    if sessao.cookie_encrypted is None or sessao.cookie_expirado():
        return False, "Cookie ausente ou expirado — Revalidar na UI e espere o login Playwright terminar."
    return True, "Sessão ativa com cookie presente."


def _iso(valor: datetime | None) -> str | None:
    return valor.isoformat() if valor is not None else None


async def montar_relatorio(db: AsyncSession, user: User) -> dict[str, Any]:
    sessao = await buscar_sessao(db, user.id)
    pronta, motivo = sessao_pronta(sessao)
    contagens = await contar(db, user.id)

    jobs = (
        await db.execute(
            select(JobLog)
            .where(JobLog.user_id == user.id)
            .order_by(JobLog.created_at.desc())
            .limit(JOBS_RECENTES)
        )
    ).scalars().all()

    intimacoes = (
        await db.execute(
            select(Intimacao)
            .where(Intimacao.user_id == user.id)
            .order_by(Intimacao.created_at.desc())
            .limit(AMOSTRAS)
        )
    ).scalars().all()

    audiencias = (
        await db.execute(
            select(Audiencia)
            .where(Audiencia.user_id == user.id)
            .order_by(Audiencia.created_at.desc())
            .limit(AMOSTRAS)
        )
    ).scalars().all()

    processos = (
        await db.execute(
            select(Processo)
            .where(Processo.user_id == user.id)
            .order_by(Processo.created_at.desc())
            .limit(AMOSTRAS)
        )
    ).scalars().all()

    notifications = (
        await db.execute(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(AMOSTRAS)
        )
    ).scalars().all()

    return {
        "email": user.email,
        "sessao": {
            "pronta": pronta,
            "motivo": motivo,
            "status": sessao.status if sessao else None,
            "tem_cookie": bool(sessao and sessao.cookie_encrypted is not None),
            "expirada": sessao.cookie_expirado() if sessao else False,
            "expires_at": _iso(sessao.expires_at) if sessao else None,
            "ultimo_erro": sessao.ultimo_erro if sessao else None,
            "ultimo_sucesso": _iso(sessao.ultimo_sucesso) if sessao else None,
        },
        "contagens": contagens,
        "job_logs": [
            {
                "tipo": job.tipo,
                "status": job.status,
                "erro": job.erro,
                "duracao_ms": job.duracao_ms,
                "created_at": _iso(job.created_at),
            }
            for job in jobs
        ],
        "intimacoes": [
            {
                "titulo": item.titulo,
                "data_movimentacao": _iso(item.data_movimentacao),
                "ciencia": item.ciencia,
                "instancia": item.instancia,
                "tem_processo_id": item.processo_id is not None,
            }
            for item in intimacoes
        ],
        "audiencias": [
            {
                "titulo": item.titulo,
                "data_audiencia": _iso(item.data_audiencia),
                "local": item.local,
                "tem_processo_id": item.processo_id is not None,
            }
            for item in audiencias
        ],
        "processos": [
            {
                "nu_processo": item.nu_processo,
                "de_classe": item.de_classe,
                "de_assunto": item.de_assunto,
                "instancia": item.instancia,
                "tem_url_cpo": bool(item.url_cpo),
                "last_synced_at": _iso(item.last_synced_at),
            }
            for item in processos
        ],
        "notifications": [
            {
                "tipo": item.tipo,
                "titulo": item.titulo,
                "is_read": item.is_read,
                "created_at": _iso(item.created_at),
            }
            for item in notifications
        ],
    }


def imprimir_relatorio(relatorio: dict[str, Any]) -> None:
    sessao = relatorio["sessao"]
    print()
    print(f"Usuario: {relatorio['email']}")
    print(f"Sessao:  status={sessao['status']} tem_cookie={sessao['tem_cookie']} expirada={sessao['expirada']} pronta={sessao['pronta']}")
    print(f"         {sessao['motivo']}")
    if sessao["expires_at"]:
        print(f"         expires_at={sessao['expires_at']}")
    if sessao["ultimo_erro"]:
        print(f"         ultimo_erro={sessao['ultimo_erro']}")

    c = relatorio["contagens"]
    print()
    print("Contagens:")
    print(
        f"  processos={c['processos']}  intimacoes={c['intimacoes']}  "
        f"audiencias={c['audiencias']}  notifications={c['notifications']}"
    )

    print()
    print("job_logs recentes:")
    if not relatorio["job_logs"]:
        print("  (nenhum)")
    for job in relatorio["job_logs"]:
        erro = f" erro={job['erro']}" if job["erro"] else ""
        print(
            f"  {job['created_at']}  {job['tipo']:18}  {job['status']:8}  "
            f"{job['duracao_ms']}ms{erro}"
        )

    print()
    print("Intimacoes (titulo/data — sem id_esaj):")
    if not relatorio["intimacoes"]:
        print("  (nenhuma)")
    for item in relatorio["intimacoes"]:
        print(
            f"  [{item['data_movimentacao']}]  {item['titulo']!r}  "
            f"ciencia={item['ciencia']}  processo={item['tem_processo_id']}"
        )

    print()
    print("Audiencias (titulo/data/local):")
    if not relatorio["audiencias"]:
        print("  (nenhuma)")
    for item in relatorio["audiencias"]:
        print(
            f"  [{item['data_audiencia']}]  {item['titulo']!r}  "
            f"local={item['local']!r}  processo={item['tem_processo_id']}"
        )

    print()
    print("Processos (numero CNJ / classe):")
    if not relatorio["processos"]:
        print("  (nenhum)")
    for item in relatorio["processos"]:
        print(
            f"  {item['nu_processo']}  {item['de_classe']!r}  "
            f"assunto={item['de_assunto']!r}  cpo={item['tem_url_cpo']}"
        )

    print()
    print("Notifications:")
    if not relatorio["notifications"]:
        print("  (nenhuma)")
    for item in relatorio["notifications"]:
        print(f"  {item['created_at']}  {item['tipo']:12}  {item['titulo']!r}")


def delta_contagens(antes: dict[str, int], depois: dict[str, int]) -> dict[str, int]:
    return {chave: depois[chave] - antes[chave] for chave in depois}


def imprimir_delta(delta: dict[str, int]) -> None:
    print()
    print("Delta desde o snapshot anterior:")
    for chave, valor in delta.items():
        sinal = "+" if valor > 0 else ""
        print(f"  {chave}: {sinal}{valor}")


def salvar_snapshot(email: str, contagens: dict[str, int]) -> None:
    SNAPSHOT_PATH.write_text(
        json.dumps(
            {"email": email, "contagens": contagens, "capturado_em": datetime.now().isoformat()},
            indent=2,
        ),
        encoding="utf-8",
    )


def carregar_snapshot() -> dict[str, Any] | None:
    if not SNAPSHOT_PATH.exists():
        return None
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
