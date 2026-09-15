"""Job diário de complemento via DataJud (Etapa 9 / ADR-015).

Diferente do ciclo de 10 min do e-SAJ, este job é **de sistema**: roda
uma vez por dia (`app/core/scheduler.py`) e itera sobre processos de
**todos** os advogados, não sobre advogados. Cada processo é isolado em
seu próprio `try/except` (`security.mdc` §8) — falha em um nunca impede
os demais.

Lote pequeno com round-robin (nunca consultado primeiro, depois o mais
atrasado) — mesmo espírito de `coleta_esaj._selecionar_lote_movimentacoes`
(ADR-012), pra não martelar a chave pública compartilhada do DataJud a
cada execução.
"""

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID

import httpx
from sqlalchemy import case, select
from sqlalchemy.engine import Row

from app.core.cnj import resolver_alias_datajud
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.job_log import (
    JOB_STATUS_FALHA,
    JOB_STATUS_SKIP,
    JOB_STATUS_SUCESSO,
    JOB_TIPO_DATAJUD,
    JobLog,
)
from app.models.processo import Processo
from app.models.processo_datajud import ProcessoDatajud
from app.schemas.datajud_raw import DatajudProcessoRaw
from app.services import datajud

logger = logging.getLogger(__name__)

# Lote generoso (job de sistema, roda 1x/dia) mas ainda limitado — a chave
# pública do DataJud é compartilhada por todo mundo que usa a API, não é
# só nossa. Round-robin entre execuções cobre a carteira toda em poucos dias.
DATAJUD_LOTE = 300
# Pequeno intervalo entre chamadas sequenciais — mesmo racional do throttle
# dos pipes e-SAJ, evita rajada na chave compartilhada.
INTERVALO_ENTRE_CONSULTAS_SEGUNDOS = 0.3

_MOTIVO_TRIBUNAL_NAO_MAPEADO = "tribunal_nao_mapeado"
_MOTIVO_ERRO_INESPERADO = "erro_inesperado"


async def _registrar_job_log(
    db, user_id: UUID, status: str, erro: str | None, inicio: datetime
) -> None:
    duracao_ms = int((datetime.now(UTC) - inicio).total_seconds() * 1000)
    db.add(
        JobLog(
            user_id=user_id,
            tipo=JOB_TIPO_DATAJUD,
            status=status,
            erro=erro,
            duracao_ms=duracao_ms,
        )
    )
    await db.commit()


async def _selecionar_lote_datajud(db, limite: int) -> list[Row]:
    """Prioriza processos nunca consultados, depois os com
    `ultima_consulta_em` mais antigo. Só processos com número CNJ
    conhecido — sem `nu_processo` não há o que consultar.
    """
    nunca_consultado = case((ProcessoDatajud.id.is_(None), 0), else_=1)
    resultado = await db.execute(
        select(Processo.id, Processo.user_id, Processo.nu_processo)
        .outerjoin(ProcessoDatajud, ProcessoDatajud.processo_id == Processo.id)
        .where(Processo.nu_processo.is_not(None))
        .order_by(nunca_consultado, ProcessoDatajud.ultima_consulta_em.asc().nulls_first())
        .limit(limite)
    )
    return list(resultado.all())


def _aplicar_resultado(registro: ProcessoDatajud, resultado: DatajudProcessoRaw) -> None:
    registro.classe_codigo = (
        str(resultado.classe.codigo)
        if resultado.classe and resultado.classe.codigo is not None
        else None
    )
    registro.classe_nome = resultado.classe.nome if resultado.classe else None
    registro.assuntos = [
        assunto.model_dump(mode="json") for assunto in resultado.assuntos
    ] or None
    registro.orgao_julgador = resultado.orgao_julgador.nome if resultado.orgao_julgador else None
    registro.data_ajuizamento = resultado.data_ajuizamento
    registro.grau = resultado.grau
    registro.formato = resultado.formato.nome if resultado.formato else None
    registro.movimentos = [
        movimento.model_dump(mode="json") for movimento in resultado.movimentos
    ] or None


async def _processar_processo(
    client: httpx.AsyncClient, processo_id: UUID, user_id: UUID, nu_processo: str | None
) -> None:
    """Consulta o DataJud para um processo e faz upsert em
    `ProcessoDatajud`. Nunca sobrescreve campos de `Processo` — só a
    tabela complementar.
    """
    inicio = datetime.now(UTC)
    async with SessionLocal() as db:
        try:
            alias = resolver_alias_datajud(nu_processo) if nu_processo else None
            if alias is None:
                await _registrar_job_log(
                    db, user_id, JOB_STATUS_SKIP, _MOTIVO_TRIBUNAL_NAO_MAPEADO, inicio
                )
                return

            resultado = await datajud.consultar_processo(client, nu_processo)
            agora = datetime.now(UTC)

            registro = await db.scalar(
                select(ProcessoDatajud).where(ProcessoDatajud.processo_id == processo_id)
            )
            if registro is None:
                registro = ProcessoDatajud(
                    processo_id=processo_id,
                    tribunal_alias=alias,
                    encontrado=False,
                    ultima_consulta_em=agora,
                )
                db.add(registro)

            registro.tribunal_alias = alias
            registro.ultima_consulta_em = agora
            registro.encontrado = resultado is not None
            if resultado is not None:
                _aplicar_resultado(registro, resultado)
        except Exception:
            await db.rollback()
            logger.exception(
                "Falha inesperada no complemento DataJud (processo_id=%s)", processo_id
            )
            await _registrar_job_log(db, user_id, JOB_STATUS_FALHA, _MOTIVO_ERRO_INESPERADO, inicio)
            return
        else:
            await _registrar_job_log(db, user_id, JOB_STATUS_SUCESSO, None, inicio)


async def job_datajud_diario() -> None:
    """Roda uma vez por dia (cron, ver `app/core/scheduler.py`): complementa
    um lote de processos (round-robin) com dados públicos do DataJud.
    Nunca lança — cada processo é isolado, e o job inteiro também está
    protegido contra falha inesperada de infraestrutura (ex.: banco fora).
    """
    if not get_settings().datajud_api_key:
        logger.info("DATAJUD_API_KEY vazio — job diário não consulta")
        return

    try:
        async with SessionLocal() as db:
            lote = await _selecionar_lote_datajud(db, DATAJUD_LOTE)
    except Exception:
        logger.exception("Falha ao selecionar lote do complemento DataJud")
        return

    if not lote:
        return

    logger.info("Complemento DataJud iniciado (processos=%d)", len(lote))
    async with httpx.AsyncClient() as client:
        for linha in lote:
            try:
                await _processar_processo(client, linha.id, linha.user_id, linha.nu_processo)
            except Exception:
                logger.exception(
                    "Complemento DataJud falhou de forma inesperada (processo_id=%s)", linha.id
                )
            await asyncio.sleep(INTERVALO_ENTRE_CONSULTAS_SEGUNDOS)
    logger.info("Complemento DataJud concluído (processos=%d)", len(lote))
