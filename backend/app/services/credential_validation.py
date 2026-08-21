"""Orquestra a validação de credenciais do e-SAJ: decripta CPF/senha em
memória, chama o motor de login do Playwright injetando a captura de
código por e-mail, persiste o resultado em `TribunalSession` e grava
`JobLog`.

Ponto único onde CPF/senha do e-SAJ ficam descriptografados — nunca em
atributo de classe, cache global ou log. Roda sob `asyncio.wait_for` com o
limite de 60s por advogado exigido pelo `security.mdc` §8; qualquer estouro
de tempo é tratado como `portal_indisponivel`.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select

from app.core.backoff import calcular_proximo_retry
from app.core.security import decrypt_secret, encrypt_secret
from app.db.session import SessionLocal
from app.models.job_log import JOB_STATUS_FALHA, JOB_STATUS_SUCESSO, JOB_TIPO_LOGIN, JobLog
from app.models.tribunal import (
    SESSION_STATUS_ATIVO,
    SESSION_STATUS_CREDENCIAL_INVALIDA,
    SESSION_STATUS_EMAIL_DESCONECTADO,
    SESSION_STATUS_PORTAL_INDISPONIVEL,
    SESSION_STATUS_REAUTH_PENDENTE,
    TRIBUNAL_ESAJ_TJSP,
    TribunalCredential,
    TribunalSession,
)
from app.services import auth_esaj, email_capture
from app.services.auth_esaj import LoginEsajError

logger = logging.getLogger(__name__)

TIMEOUT_VALIDACAO_SEGUNDOS = 60
SESSAO_EXPIRA_HORAS = 22

# Nível de processo: evita duas validações concorrentes do mesmo advogado
# (ex.: clique duplo em "Revalidar" antes da primeira tentativa terminar).
# Não sobrevive a restart nem é compartilhado entre workers — é só uma
# proteção best-effort dentro do processo atual.
_VALIDACOES_EM_ANDAMENTO: set[UUID] = set()


def validacao_em_andamento(user_id: UUID) -> bool:
    """True enquanto `validar_credencial_esaj` está rodando para este
    advogado neste processo. O scheduler usa isso para não disparar pipes
    no mesmo instante em que o Playwright está anulando o cookie (choque
    das 1h entre renovação noturna e ciclo de 10 min).
    """
    return user_id in _VALIDACOES_EM_ANDAMENTO


async def _buscar_ou_criar_sessao(db, user_id: UUID) -> TribunalSession:
    sessao = await db.scalar(
        select(TribunalSession).where(
            TribunalSession.user_id == user_id,
            TribunalSession.tribunal == TRIBUNAL_ESAJ_TJSP,
        )
    )
    if sessao is None:
        sessao = TribunalSession(user_id=user_id, tribunal=TRIBUNAL_ESAJ_TJSP, cookie_encrypted=None)
        db.add(sessao)
    return sessao


async def _registrar_job_log(
    db, user_id: UUID, job_tipo: str, status: str, erro: str | None, inicio: datetime
) -> None:
    duracao_ms = int((datetime.now(UTC) - inicio).total_seconds() * 1000)
    db.add(JobLog(user_id=user_id, tipo=job_tipo, status=status, erro=erro, duracao_ms=duracao_ms))
    await db.commit()


async def _marcar_falha(
    db,
    sessao: TribunalSession,
    credencial: TribunalCredential,
    user_id: UUID,
    erro_tipo: str,
    inicio: datetime,
    job_tipo: str,
) -> None:
    sessao.anular_cookie()
    sessao.status = erro_tipo
    sessao.ultimo_erro = erro_tipo
    sessao.tentativas_falha += 1
    sessao.proximo_retry = calcular_proximo_retry(sessao.tentativas_falha)
    if erro_tipo == SESSION_STATUS_CREDENCIAL_INVALIDA:
        # Para de tentar sozinho até o advogado corrigir a senha —
        # demais erros (portal fora do ar, e-mail desconectado no
        # meio da tentativa, bloqueio temporário) mantêm a
        # credencial ativa para novas tentativas.
        credencial.is_active = False
    await db.commit()
    await _registrar_job_log(db, user_id, job_tipo, JOB_STATUS_FALHA, erro_tipo, inicio)
    logger.info("Validação e-SAJ falhou (user_id=%s, tipo=%s)", user_id, erro_tipo)


async def validar_credencial_esaj(user_id: UUID, *, job_tipo: str = JOB_TIPO_LOGIN) -> None:
    """Executa uma tentativa completa de login no e-SAJ para `user_id` e
    grava o resultado no banco. Nunca levanta exceção para quem chamou (é
    disparada como `BackgroundTask` ou pelo scheduler — não há ninguém para
    tratar um erro aqui além de logar e deixar `TribunalSession.status`
    refletir a falha).

    `job_tipo` só afeta o `JobLog` gravado (`login` para disparo do
    advogado via `/credentials/esaj` ou `/revalidar`, `reauth` para o cron
    noturno do scheduler) — a lógica de validação é idêntica nos dois casos.
    """
    if user_id in _VALIDACOES_EM_ANDAMENTO:
        logger.info("Validação e-SAJ já em andamento para user_id=%s — disparo ignorado", user_id)
        return
    _VALIDACOES_EM_ANDAMENTO.add(user_id)

    inicio = datetime.now(UTC)
    cpf: str | None = None
    senha: str | None = None
    try:
        async with SessionLocal() as db:
            try:
                credencial = await db.scalar(
                    select(TribunalCredential).where(
                        TribunalCredential.user_id == user_id,
                        TribunalCredential.tribunal == TRIBUNAL_ESAJ_TJSP,
                    )
                )
                if credencial is None:
                    logger.info("Credencial e-SAJ removida antes da validação (user_id=%s)", user_id)
                    return

                sessao = await _buscar_ou_criar_sessao(db, user_id)
                sessao.status = SESSION_STATUS_REAUTH_PENDENTE
                sessao.anular_cookie()
                await db.commit()

                if credencial.email_provider is None:
                    await _marcar_falha(
                        db, sessao, credencial, user_id, SESSION_STATUS_EMAIL_DESCONECTADO, inicio, job_tipo
                    )
                    return

                cancelado = asyncio.Event()

                async def obter_codigo(since: datetime) -> str:
                    return await email_capture.buscar_codigo_esaj(
                        user_id, since, cancelado=cancelado
                    )

                try:
                    cpf = decrypt_secret(credencial.cpf_encrypted)
                    senha = decrypt_secret(credencial.senha_encrypted)

                    cookies = await asyncio.wait_for(
                        auth_esaj.realizar_login(cpf, senha, obter_codigo=obter_codigo),
                        timeout=TIMEOUT_VALIDACAO_SEGUNDOS,
                    )
                except TimeoutError:
                    cancelado.set()
                    erro_tipo = SESSION_STATUS_PORTAL_INDISPONIVEL
                except LoginEsajError as exc:
                    erro_tipo = exc.tipo
                except Exception:
                    # Nunca deixar a sessão presa em `reauth_pendente` nem
                    # explodir a BackgroundTask do Starlette.
                    logger.exception(
                        "Erro inesperado na validação e-SAJ (user_id=%s)", user_id
                    )
                    erro_tipo = SESSION_STATUS_PORTAL_INDISPONIVEL
                else:
                    sessao.status = SESSION_STATUS_ATIVO
                    sessao.cookie_encrypted = encrypt_secret(json.dumps(cookies))
                    sessao.expires_at = datetime.now(UTC) + timedelta(hours=SESSAO_EXPIRA_HORAS)
                    sessao.ultimo_sucesso = datetime.now(UTC)
                    sessao.ultimo_erro = None
                    sessao.tentativas_falha = 0
                    sessao.proximo_retry = None
                    credencial.last_validated_at = datetime.now(UTC)
                    credencial.is_active = True
                    await db.commit()
                    await _registrar_job_log(db, user_id, job_tipo, JOB_STATUS_SUCESSO, None, inicio)
                    logger.info("Validação e-SAJ concluída com sucesso (user_id=%s)", user_id)
                    return

                await _marcar_falha(db, sessao, credencial, user_id, erro_tipo, inicio, job_tipo)
            except Exception:
                # Última rede: falha ao gravar status, commit, etc. Tenta
                # ainda assim marcar portal_indisponivel para o polling parar.
                logger.exception(
                    "Falha crítica na validação e-SAJ (user_id=%s) — tentando marcar portal_indisponivel",
                    user_id,
                )
                try:
                    sessao = await _buscar_ou_criar_sessao(db, user_id)
                    sessao.anular_cookie()
                    sessao.status = SESSION_STATUS_PORTAL_INDISPONIVEL
                    sessao.ultimo_erro = SESSION_STATUS_PORTAL_INDISPONIVEL
                    await db.commit()
                except Exception:
                    logger.exception(
                        "Não foi possível marcar portal_indisponivel (user_id=%s)", user_id
                    )
    finally:
        _VALIDACOES_EM_ANDAMENTO.discard(user_id)
        cpf = None
        senha = None
