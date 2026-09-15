"""Testes de app.core.scheduler — só a configuração dos triggers.

Cada teste usa uma instância nova de `AsyncIOScheduler` (via monkeypatch no
singleton do módulo) para não vazar jobs/estado entre testes — e como
fixture assíncrona, para que o `shutdown()` rode antes do loop de eventos
do teste ser fechado pelo pytest-asyncio.
"""

from datetime import timedelta

import pytest
import pytest_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

import app.core.scheduler as scheduler_module
from app.core.scheduler import (
    JOB_ID_CICLO_PIPES,
    JOB_ID_DATAJUD_DIARIO,
    JOB_ID_RENOVACAO_DIARIA,
    TIMEZONE_BRASILIA,
)


@pytest_asyncio.fixture()
async def fresh_scheduler(monkeypatch: pytest.MonkeyPatch):
    novo = AsyncIOScheduler(timezone=TIMEZONE_BRASILIA)
    monkeypatch.setattr(scheduler_module, "scheduler", novo)
    yield novo
    if novo.running:
        novo.shutdown(wait=False)


class TestIniciarScheduler:
    @pytest.mark.asyncio
    async def test_job_diario_usa_cron_1h_america_sao_paulo(self, fresh_scheduler):
        scheduler_module.iniciar_scheduler()

        job = fresh_scheduler.get_job(JOB_ID_RENOVACAO_DIARIA)

        assert job is not None
        assert isinstance(job.trigger, CronTrigger)
        assert job.trigger.timezone == TIMEZONE_BRASILIA
        campos = {campo.name: str(campo) for campo in job.trigger.fields}
        assert campos["hour"] == "1"
        assert campos["minute"] == "0"

    @pytest.mark.asyncio
    async def test_job_de_pipes_usa_interval_de_10_minutos(self, fresh_scheduler):
        scheduler_module.iniciar_scheduler()

        job = fresh_scheduler.get_job(JOB_ID_CICLO_PIPES)

        assert job is not None
        assert isinstance(job.trigger, IntervalTrigger)
        assert job.trigger.interval == timedelta(minutes=10)

    @pytest.mark.asyncio
    async def test_job_datajud_usa_cron_3h_america_sao_paulo(self, fresh_scheduler):
        scheduler_module.iniciar_scheduler()

        job = fresh_scheduler.get_job(JOB_ID_DATAJUD_DIARIO)

        assert job is not None
        assert isinstance(job.trigger, CronTrigger)
        assert job.trigger.timezone == TIMEZONE_BRASILIA
        campos = {campo.name: str(campo) for campo in job.trigger.fields}
        assert campos["hour"] == "3"
        assert campos["minute"] == "0"

    @pytest.mark.asyncio
    async def test_e_idempotente_nao_duplica_jobs(self, fresh_scheduler):
        scheduler_module.iniciar_scheduler()
        scheduler_module.iniciar_scheduler()

        assert len(fresh_scheduler.get_jobs()) == 3

    @pytest.mark.asyncio
    async def test_todos_os_jobs_tem_max_instances_1(self, fresh_scheduler):
        scheduler_module.iniciar_scheduler()

        for job_id in (JOB_ID_RENOVACAO_DIARIA, JOB_ID_CICLO_PIPES, JOB_ID_DATAJUD_DIARIO):
            job = fresh_scheduler.get_job(job_id)
            assert job.max_instances == 1
