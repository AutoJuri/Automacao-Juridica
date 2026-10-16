"""Rotas do painel de processos.

`user_id` vem só do JWT. Processo de outro advogado responde 404 (não 403)
para não vazar existência. `id_esaj` nunca sai no JSON.
"""

import logging
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import LIMITE_CONSULTA_PUBLICA, limiter
from app.schemas.consulta_publica import ConsultaPublicaSchema
from app.schemas.processo import (
    AudienciaPainelSchema,
    IntimacaoPainelSchema,
    ProcessoDetalheSchema,
    ProcessoFixadoSchema,
    ProcessoFixarSchema,
    ProcessoListSchema,
)
from app.services import datajud, painel
from app.services.consulta_publica import montar_consulta_publica

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/processos", tags=["processos"])

_NAO_ENCONTRADO = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado")


@router.get("", response_model=list[ProcessoListSchema])
async def listar_processos(
    current_user: CurrentUser,
    db: DbSession,
    q: str | None = Query(default=None, max_length=120),
) -> list[ProcessoListSchema]:
    return await painel.listar_processos(db, current_user.id, q=q)


@router.get("/publico", response_model=ConsultaPublicaSchema)
@limiter.limit(LIMITE_CONSULTA_PUBLICA)
async def consultar_publico(
    request: Request,
    current_user: CurrentUser,
    numero: str = Query(min_length=20, max_length=30),
) -> ConsultaPublicaSchema:
    """Ficha pública de um CNJ que pode não ser da carteira. Não grava nada.

    `current_user` só garante login. O número não precisa ser de um processo
    deste usuário — é exatamente o caso de uso.
    """
    logger.info("Consulta pública de CNJ para user_id=%s", current_user.id)
    async with httpx.AsyncClient() as client:
        exibicao = await datajud.consultar_exibicao(client, numero.strip())
    if exibicao.situacao == "numero_invalido":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Informe um número CNJ completo",
        )
    if exibicao.situacao == "sem_chave":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A consulta pública ainda não está configurada",
        )
    return montar_consulta_publica(numero, exibicao)


@router.get("/{processo_id}", response_model=ProcessoDetalheSchema)
async def obter_processo(
    processo_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ProcessoDetalheSchema:
    detalhe = await painel.buscar_processo_detalhe(db, current_user.id, processo_id)
    if detalhe is None:
        raise _NAO_ENCONTRADO
    return detalhe


@router.patch("/{processo_id}", response_model=ProcessoFixadoSchema)
async def fixar_processo(
    processo_id: UUID,
    body: ProcessoFixarSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ProcessoFixadoSchema:
    atualizado = await painel.atualizar_fixado(
        db, current_user.id, processo_id, fixado=body.fixado
    )
    if atualizado is None:
        raise _NAO_ENCONTRADO
    return ProcessoFixadoSchema(id=atualizado.id, fixado=atualizado.fixado)


router_intimacoes = APIRouter(prefix="/intimacoes", tags=["processos"])
router_audiencias = APIRouter(prefix="/audiencias", tags=["processos"])


@router_intimacoes.get("", response_model=list[IntimacaoPainelSchema])
async def listar_intimacoes(
    current_user: CurrentUser,
    db: DbSession,
) -> list[IntimacaoPainelSchema]:
    return await painel.listar_intimacoes_painel(db, current_user.id)


@router_audiencias.get("", response_model=list[AudienciaPainelSchema])
async def listar_audiencias(
    current_user: CurrentUser,
    db: DbSession,
) -> list[AudienciaPainelSchema]:
    return await painel.listar_audiencias_painel(db, current_user.id)
