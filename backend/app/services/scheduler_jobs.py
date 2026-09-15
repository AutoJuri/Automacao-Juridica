"""Pontos de entrada chamados pelo APScheduler (`app/core/scheduler.py`).

Dois jobs, exatamente como o PRD pede:

- `job_renovacao_diaria`: roda 1x/dia (cron, 1h da manhã em
  America/Sao_Paulo) e renova o cookie de **todos** os advogados com
  credencial ativa, independente do status atual da sessão.
- `job_ciclo_dez_minutos`: roda a cada 10 minutos; para cada advogado com
  credencial ativa decide, com base no status atual de `tribunal_sessions`,
  se roda o ciclo de pipes (`coleta_esaj.executar_ciclo_usuario`) ou
  dispara uma reautenticação (`credential_validation.validar_credencial_esaj`)
  — cobre o "se cookie inválido, agenda reautenticação imediata" do PRD sem
  precisar de um terceiro job. Ver ADR-011.

Cada advogado é isolado em seu próprio `try/except` (`security.mdc` §8) —
falha em um nunca impede os demais.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select

from app.db.session import SessionLocal
from app.models.job_log import JOB_TIPO_REAUTH
from app.models.tribunal import (
    SESSION_STATUS_ATIVO,
    SESSION_STATUS_BLOQUEADO,
    SESSION_STATUS_CODIGO_NAO_ENCONTRADO,
    SESSION_STATUS_EMAIL_DESCONECTADO,
    SESSION_STATUS_PORTAL_INDISPONIVEL,
    SESSION_STATUS_REAUTH_PENDENTE,
    TRIBUNAL_ESAJ_TJSP,
    TribunalCredential,
    TribunalSession,
)
from app.services.coleta_esaj import executar_ciclo_usuario
from app.services.credential_validation import validacao_em_andamento, validar_credencial_esaj

logger = logging.getLogger(__name__)

# Status de erro que, uma vez o backoff (`proximo_retry`) passado, merecem
# uma nova tentativa de login completo (o cookie não é confiável nesses
# casos — diferente de `bloqueado`, que é só rate limit).
_STATUS_ELEGIVEIS_PARA_REAUTH = (
    SESSION_STATUS_EMAIL_DESCONECTADO,
    SESSION_STATUS_PORTAL_INDISPONIVEL,
    SESSION_STATUS_CODIGO_NAO_ENCONTRADO,
)


def _backoff_expirado(sessao: TribunalSession, agora: datetime) -> bool:
    return sessao.proximo_retry is None or sessao.proximo_retry <= agora


async def _reativar_apos_bloqueio(user_id: UUID) -> None:
    """Volta a sessão para `ativo` mantendo o cookie — usado só quando o
    backoff de rate limit já passou. Reconsulta o status no banco (em vez
    de confiar no valor lido para a decisão) para não sobrescrever uma
    mudança concorrente (ex.: alguém clicou "Revalidar" nesse meio tempo).
    """
    async with SessionLocal() as db:
        sessao = await db.scalar(
            select(TribunalSession).where(
                TribunalSession.user_id == user_id,
                TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
            )
        )
        if sessao is not None and sessao.status == SESSION_STATUS_BLOQUEADO:
            sessao.status = SESSION_STATUS_ATIVO
            await db.commit()


async def _processar_advogado(user_id: UUID, sessao: TribunalSession | None, agora: datetime) -> None:
    # Playwright já está anulando/trocando o cookie deste advogado (renovação
    # noturna, Revalidar, ou tick anterior). Pipes neste instante usariam um
    # cookie prestes a morrer — espera o próximo ciclo.
    if validacao_em_andamento(user_id):
        return

    if sessao is None:
        # Credencial ativa sem sessão nenhuma — nunca validou ou a sessão
        # foi apagada por algum motivo. Só um login completo resolve.
        await validar_credencial_esaj(user_id, job_tipo=JOB_TIPO_REAUTH)
        return

    if sessao.status == SESSION_STATUS_ATIVO:
        if sessao.cookie_expirado():
            await validar_credencial_esaj(user_id, job_tipo=JOB_TIPO_REAUTH)
            return
        await executar_ciclo_usuario(user_id)
        return

    if sessao.status == SESSION_STATUS_BLOQUEADO:
        if not _backoff_expirado(sessao, agora):
            return
        await _reativar_apos_bloqueio(user_id)
        await executar_ciclo_usuario(user_id)
        return

    if sessao.status == SESSION_STATUS_REAUTH_PENDENTE:
        # Sem espera de 5 min: duplicata no mesmo processo já é barrada por
        # `_VALIDACOES_EM_ANDAMENTO`. Depois de um restart, retentar na hora
        # fecha o gap da ADR-008.
        await validar_credencial_esaj(user_id, job_tipo=JOB_TIPO_REAUTH)
        return

    if sessao.status in _STATUS_ELEGIVEIS_PARA_REAUTH:
        if not _backoff_expirado(sessao, agora):
            return
        await validar_credencial_esaj(user_id, job_tipo=JOB_TIPO_REAUTH)
        return

    # `credencial_invalida` não deveria aparecer aqui — `is_active=False`
    # tira o advogado do filtro da query. Se acontecer por alguma corrida,
    # não fazemos nada (evita insistir numa senha que o advogado já trocou).


async def job_ciclo_dez_minutos() -> None:
    """Job de 10 em 10 minutos: pipes para quem está ativo, reautenticação
    para quem precisa e respeita o backoff de quem está temporariamente
    bloqueado ou com erro recente.
    """
    async with SessionLocal() as db:
        resultado = await db.execute(
            select(TribunalCredential, TribunalSession)
            .outerjoin(
                TribunalSession,
                and_(
                    TribunalSession.user_id == TribunalCredential.user_id,
                    TribunalSession.tribunal == TribunalCredential.tribunal,
                ),
            )
            .where(
                TribunalCredential.tribunal == TRIBUNAL_ESAJ_TJSP,
                TribunalCredential.is_active.is_(True),
            )
        )
        linhas = resultado.all()

    agora = datetime.now(UTC)
    for credencial, sessao in linhas:
        try:
            await _processar_advogado(credencial.user_id, sessao, agora)
        except Exception:
            logger.exception(
                "Ciclo de 10 minutos falhou de forma inesperada (user_id=%s)", credencial.user_id
            )


async def job_renovacao_diaria() -> None:
    """Job diário (1h da manhã em America/Sao_Paulo): renova o cookie de
    todos os advogados com credencial ativa, independente do status atual
    da sessão — reforça a sessão antes do primeiro ciclo de pipes do dia.
    """
    async with SessionLocal() as db:
        resultado = await db.execute(
            select(TribunalCredential.user_id).where(
                TribunalCredential.tribunal == TRIBUNAL_ESAJ_TJSP,
                TribunalCredential.is_active.is_(True),
            )
        )
        user_ids = list(resultado.scalars().all())

    logger.info("Renovação noturna do e-SAJ iniciada (advogados=%d)", len(user_ids))
    for user_id in user_ids:
        try:
            await validar_credencial_esaj(user_id, job_tipo=JOB_TIPO_REAUTH)
        except Exception:
            logger.exception("Renovação noturna falhou de forma inesperada (user_id=%s)", user_id)
    logger.info("Renovação noturna do e-SAJ concluída (advogados=%d)", len(user_ids))
