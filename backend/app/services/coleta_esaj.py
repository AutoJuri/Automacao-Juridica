"""Orquestra o ciclo de coleta e-SAJ: intimações → audiências → upsert de
ficha → diff → notificações (ADR-010 — sem petições, sem movimentações).

Decripta o cookie de sessão só em memória, aqui, e descarta assim que o
ciclo termina — nunca em atributo de classe, cache global ou log (ver
`security.mdc` §8). Roda sob `asyncio.wait_for` com o limite de 60s por
advogado; qualquer estouro de tempo é tratado como falha do próprio pipe
em andamento, sem invalidar a sessão (o cookie pode continuar bom).

`executar_ciclo_usuario` é reaproveitado pelo scheduler
(`app/services/scheduler_jobs.py`), que decide por advogado se roda o
ciclo de pipes ou dispara reautenticação — ver ADR-011.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import select

from app.core.backoff import calcular_proximo_retry
from app.core.security import decrypt_secret
from app.db.session import SessionLocal
from app.etl.diff import (
    completar_processo_id_map,
    diff_e_persistir_audiencias,
    diff_e_persistir_intimacoes,
    gerar_notificacoes,
    upsert_processos,
)
from app.models.job_log import (
    JOB_STATUS_FALHA,
    JOB_STATUS_SKIP,
    JOB_STATUS_SUCESSO,
    JOB_TIPO_PIPE_AUDIENCIAS,
    JOB_TIPO_PIPE_INTIMACOES,
    JOB_TIPO_PIPE_PROCESSOS,
    JobLog,
)
from app.models.processo import Processo
from app.models.tribunal import (
    SESSION_STATUS_ATIVO,
    SESSION_STATUS_BLOQUEADO,
    SESSION_STATUS_REAUTH_PENDENTE,
    TRIBUNAL_ESAJ_TJSP,
    TribunalSession,
)
from app.schemas.esaj_raw import AudienciaRaw, IntimacaoRaw, ProcessoRaw
from app.services.esaj_http import (
    EsajPortalIndisponivelError,
    EsajRateLimitError,
    EsajSessaoInvalidaError,
    montar_client,
)
from app.services.pipes import pipe_audiencias, pipe_intimacoes, pipe_processos

logger = logging.getLogger(__name__)

TIMEOUT_CICLO_SEGUNDOS = 60

ERRO_SESSAO_INVALIDA = "sessao_invalida"
ERRO_PORTAL = "erro_portal"
ERRO_RATE_LIMIT = "rate_limited"
ERRO_INESPERADO = "erro_inesperado"


async def _registrar_job_log(
    db, user_id: UUID, tipo: str, status: str, erro: str | None, inicio: datetime
) -> None:
    duracao_ms = int((datetime.now(UTC) - inicio).total_seconds() * 1000)
    db.add(JobLog(user_id=user_id, tipo=tipo, status=status, erro=erro, duracao_ms=duracao_ms))
    await db.commit()


async def _coletar_pipe(
    db,
    sessao: TribunalSession,
    user_id: UUID,
    tipo_job: str,
    corrotina,
):
    """Roda um pipe, grava o `JobLog` correspondente e — só quando a
    resposta indica sessão inválida — marca `reauth_pendente` e anula o
    cookie. Nunca deixa uma exceção crua escapar para o chamador.
    """
    inicio = datetime.now(UTC)
    try:
        resultado = await corrotina
    except EsajSessaoInvalidaError:
        sessao.status = SESSION_STATUS_REAUTH_PENDENTE
        sessao.anular_cookie()
        await db.commit()
        await _registrar_job_log(db, user_id, tipo_job, JOB_STATUS_FALHA, ERRO_SESSAO_INVALIDA, inicio)
        logger.info("Sessão e-SAJ invalidada durante coleta (user_id=%s, tipo=%s)", user_id, tipo_job)
        return None
    except EsajRateLimitError:
        # Rate limit não invalida o cookie — só bloqueia temporariamente.
        # `job_ciclo_dez_minutos` retoma os pipes direto (sem reauth) assim
        # que `proximo_retry` passar.
        sessao.status = SESSION_STATUS_BLOQUEADO
        sessao.tentativas_falha += 1
        sessao.proximo_retry = calcular_proximo_retry(sessao.tentativas_falha)
        await db.commit()
        await _registrar_job_log(db, user_id, tipo_job, JOB_STATUS_FALHA, ERRO_RATE_LIMIT, inicio)
        logger.info("Rate limit do e-SAJ durante coleta (user_id=%s, tipo=%s)", user_id, tipo_job)
        return None
    except EsajPortalIndisponivelError as exc:
        await _registrar_job_log(db, user_id, tipo_job, JOB_STATUS_FALHA, ERRO_PORTAL, inicio)
        logger.info(
            "Pipe e-SAJ falhou (user_id=%s, tipo=%s, causa=%s)", user_id, tipo_job, type(exc).__name__
        )
        return None
    except Exception:
        await _registrar_job_log(db, user_id, tipo_job, JOB_STATUS_FALHA, ERRO_INESPERADO, inicio)
        logger.exception("Erro inesperado no pipe e-SAJ (user_id=%s, tipo=%s)", user_id, tipo_job)
        return None
    else:
        if sessao.tentativas_falha > 0 or sessao.proximo_retry is not None:
            # Recuperou de um rate limit anterior no mesmo advogado — limpa o
            # bookkeeping de backoff para não escalar à toa na próxima falha.
            sessao.tentativas_falha = 0
            sessao.proximo_retry = None
            await db.commit()
        await _registrar_job_log(db, user_id, tipo_job, JOB_STATUS_SUCESSO, None, inicio)
        return resultado


async def _skip_pipe(db, user_id: UUID, tipo_job: str, sessao: TribunalSession) -> None:
    motivo = ERRO_RATE_LIMIT if sessao.status == SESSION_STATUS_BLOQUEADO else ERRO_SESSAO_INVALIDA
    await _registrar_job_log(db, user_id, tipo_job, JOB_STATUS_SKIP, motivo, datetime.now(UTC))


async def _cds_processo_persistidos(db, user_id: UUID) -> set[str]:
    resultado = await db.execute(select(Processo.cd_processo).where(Processo.user_id == user_id))
    return set(resultado.scalars().all())


async def _executar_ciclo(db, user_id: UUID, sessao: TribunalSession, client: httpx.AsyncClient) -> None:
    intimacoes_raw: list[IntimacaoRaw] | None = await _coletar_pipe(
        db, sessao, user_id, JOB_TIPO_PIPE_INTIMACOES, pipe_intimacoes.coletar(client)
    )
    if sessao.status != SESSION_STATUS_ATIVO:
        await _skip_pipe(db, user_id, JOB_TIPO_PIPE_AUDIENCIAS, sessao)
        await _skip_pipe(db, user_id, JOB_TIPO_PIPE_PROCESSOS, sessao)
        return

    audiencias_raw: list[AudienciaRaw] | None = await _coletar_pipe(
        db, sessao, user_id, JOB_TIPO_PIPE_AUDIENCIAS, pipe_audiencias.coletar(client)
    )
    if sessao.status != SESSION_STATUS_ATIVO:
        await _skip_pipe(db, user_id, JOB_TIPO_PIPE_PROCESSOS, sessao)
        return

    intimacoes_raw = intimacoes_raw or []
    audiencias_raw = audiencias_raw or []

    cds_processo = {raw.cd_processo for raw in intimacoes_raw} | {raw.cd_processo for raw in audiencias_raw}
    cds_processo |= await _cds_processo_persistidos(db, user_id)

    processos_raw: list[ProcessoRaw] | None = await _coletar_pipe(
        db,
        sessao,
        user_id,
        JOB_TIPO_PIPE_PROCESSOS,
        pipe_processos.coletar(client, sorted(cds_processo)),
    )
    processos_raw = processos_raw or []

    processo_id_por_cd = await upsert_processos(db, user_id, processos_raw)
    processo_id_por_cd = await completar_processo_id_map(db, user_id, cds_processo, processo_id_por_cd)

    novas_intimacoes = await diff_e_persistir_intimacoes(db, user_id, intimacoes_raw, processo_id_por_cd)
    novas_audiencias = await diff_e_persistir_audiencias(db, user_id, audiencias_raw, processo_id_por_cd)
    await gerar_notificacoes(db, user_id, novas_intimacoes, novas_audiencias)
    await db.commit()


async def executar_ciclo_usuario(user_id: UUID) -> None:
    """Executa um ciclo completo de coleta e-SAJ para `user_id`. Nunca
    levanta exceção — é pensada para ser chamada isoladamente por advogado
    pelo scheduler, sem que a falha de um afete os demais.
    """
    async with SessionLocal() as db:
        cookies: dict[str, str] | None = None
        try:
            sessao = await db.scalar(
                select(TribunalSession).where(
                    TribunalSession.user_id == user_id,
                    TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
                )
            )
            if (
                sessao is None
                or sessao.status != SESSION_STATUS_ATIVO
                or sessao.cookie_encrypted is None
                or sessao.cookie_expirado()
            ):
                return

            cookies = json.loads(decrypt_secret(sessao.cookie_encrypted))
            async with montar_client(cookies) as client:
                try:
                    await asyncio.wait_for(
                        _executar_ciclo(db, user_id, sessao, client), timeout=TIMEOUT_CICLO_SEGUNDOS
                    )
                except TimeoutError:
                    logger.warning(
                        "Ciclo de coleta e-SAJ excedeu %ss (user_id=%s)", TIMEOUT_CICLO_SEGUNDOS, user_id
                    )
        except Exception:
            logger.exception("Falha inesperada no ciclo de coleta e-SAJ (user_id=%s)", user_id)
        finally:
            cookies = None


async def executar_ciclo_todos_usuarios() -> None:
    """Roda o ciclo de coleta para todos os advogados com sessão `ativo` e
    cookie presente. Isola falhas por advogado (`security.mdc` §8).

    Uso direto (scripts de teste manual, ex.: `disparar_coleta.py`) — o
    scheduler usa `scheduler_jobs.job_ciclo_dez_minutos`, que também decide
    reautenticação para sessões não-ativas antes de rodar os pipes.
    """
    async with SessionLocal() as db:
        resultado = await db.execute(
            select(TribunalSession.user_id).where(
                TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
                TribunalSession.status == SESSION_STATUS_ATIVO,
                TribunalSession.cookie_encrypted.is_not(None),
            )
        )
        user_ids = list(resultado.scalars().all())

    for user_id in user_ids:
        try:
            await executar_ciclo_usuario(user_id)
        except Exception:
            logger.exception("Ciclo de coleta e-SAJ falhou de forma inesperada (user_id=%s)", user_id)
