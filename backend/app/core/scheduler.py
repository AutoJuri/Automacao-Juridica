"""APScheduler dentro do próprio processo FastAPI — dois jobs (renovação
noturna de cookie + ciclo de pipes a cada 10 minutos), ver
`app/services/scheduler_jobs.py` para a lógica de cada um.

Timezone explícito (`America/Sao_Paulo`) no trigger do cron, não no
sistema operacional: o container roda no Railway em UTC, então "1h da
manhã" sem timezone explícito dispararia às 1h UTC (22h em Brasília) —
ver ADR-011.
"""

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.scheduler_jobs import job_ciclo_dez_minutos, job_renovacao_diaria

logger = logging.getLogger(__name__)

TIMEZONE_BRASILIA = ZoneInfo("America/Sao_Paulo")

HORA_RENOVACAO_DIARIA = 1
MINUTO_RENOVACAO_DIARIA = 0
MINUTOS_CICLO_PIPES = 10

JOB_ID_RENOVACAO_DIARIA = "renovacao_diaria_esaj"
JOB_ID_CICLO_PIPES = "ciclo_pipes_esaj"

scheduler = AsyncIOScheduler(timezone=TIMEZONE_BRASILIA)


def iniciar_scheduler() -> None:
    """Registra os dois jobs e inicia o scheduler. Idempotente: pode ser
    chamado de novo (ex.: reload em dev) sem duplicar jobs, graças a
    `replace_existing=True`.

    `max_instances=1` + `coalesce=True` em ambos: se uma execução atrasar
    (ex.: muitos advogados no ciclo de 10min), a próxima disparada não roda
    em paralelo — só recupera o atraso quando a anterior terminar.
    """
    scheduler.add_job(
        job_renovacao_diaria,
        trigger=CronTrigger(
            hour=HORA_RENOVACAO_DIARIA,
            minute=MINUTO_RENOVACAO_DIARIA,
            timezone=TIMEZONE_BRASILIA,
        ),
        id=JOB_ID_RENOVACAO_DIARIA,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        job_ciclo_dez_minutos,
        trigger=IntervalTrigger(minutes=MINUTOS_CICLO_PIPES),
        id=JOB_ID_CICLO_PIPES,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info(
        "Scheduler iniciado (renovação diária às %02d:%02d America/Sao_Paulo, ciclo de pipes a cada %dmin)",
        HORA_RENOVACAO_DIARIA,
        MINUTO_RENOVACAO_DIARIA,
        MINUTOS_CICLO_PIPES,
    )


def parar_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler parado")
