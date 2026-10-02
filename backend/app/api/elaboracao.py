"""Rotas da IA da elaboração (ADR-016).

`user_id` vem só do JWT. Elaboração/processo de outro advogado responde
404 (não 403) para não vazar existência — mesmo padrão de `processos.py`.
Nenhum schema de resposta expõe campo `*_encrypted`.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import LIMITE_ELABORACAO_GERAR, limiter
from app.schemas.elaboracao import (
    EditarMinutaSchema,
    ElaboracaoCreateSchema,
    ElaboracaoPublicSchema,
    EstiloTextoSchema,
    FatosExtrasUpdateSchema,
    SugestaoPecaSchema,
    VersaoMinutaPublicSchema,
)
from app.services import elaboracao as elaboracao_service
from app.services.llm.base import LLMLimiteAtingidoError
from app.services.llm.openrouter_provider import LLMProviderNaoConfiguradoError

router = APIRouter(prefix="/elaboracoes", tags=["elaboracao"])

_NAO_ENCONTRADA = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Elaboração não encontrada"
)
_PROCESSO_NAO_ENCONTRADO = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Processo não encontrado"
)
_SEM_VERSAO_ANTERIOR = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Gere a primeira versão (Elaborar) antes de editar.",
)
_VERSAO_ILEGIVEL = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="A minuta anterior não pode ser lida.",
)
_COTA_MODELO = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="Cota do modelo esgotada no momento.",
)
_MODELO_NAO_CONFIGURADO = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="O modelo de IA configurado não pode ser usado neste ambiente.",
)


@router.post("", response_model=ElaboracaoPublicSchema, status_code=status.HTTP_201_CREATED)
async def criar_ou_buscar_elaboracao(
    body: ElaboracaoCreateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ElaboracaoPublicSchema:
    resultado = await elaboracao_service.obter_ou_criar_elaboracao(
        db, current_user.id, processo_id=body.processo_id, peca=body.peca
    )
    if resultado is None:
        raise _PROCESSO_NAO_ENCONTRADO
    return resultado


@router.get("/sugestao-peca", response_model=SugestaoPecaSchema)
@limiter.limit(LIMITE_ELABORACAO_GERAR)
async def sugestao_peca(
    request: Request,
    processo_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> SugestaoPecaSchema:
    try:
        resultado = await elaboracao_service.sugerir_peca_para_processo(
            db, current_user.id, processo_id
        )
    except LLMProviderNaoConfiguradoError as exc:
        raise _MODELO_NAO_CONFIGURADO from exc
    if resultado is None:
        raise _PROCESSO_NAO_ENCONTRADO
    return resultado


@router.patch("/{elaboracao_id}", response_model=ElaboracaoPublicSchema)
async def atualizar_fatos_extras(
    elaboracao_id: UUID,
    body: FatosExtrasUpdateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ElaboracaoPublicSchema:
    resultado = await elaboracao_service.atualizar_fatos_extras(
        db, current_user.id, elaboracao_id, fatos_extras=body.fatos_extras
    )
    if resultado is None:
        raise _NAO_ENCONTRADA
    return resultado


@router.post("/{elaboracao_id}/gerar", response_model=VersaoMinutaPublicSchema)
@limiter.limit(LIMITE_ELABORACAO_GERAR)
async def gerar_minuta(
    request: Request,
    elaboracao_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> VersaoMinutaPublicSchema:
    try:
        resultado = await elaboracao_service.gerar_primeira_versao(
            db, current_user.id, elaboracao_id
        )
    except LLMLimiteAtingidoError as exc:
        raise _COTA_MODELO from exc
    except LLMProviderNaoConfiguradoError as exc:
        raise _MODELO_NAO_CONFIGURADO from exc
    if resultado is None:
        raise _NAO_ENCONTRADA
    return resultado


@router.post("/{elaboracao_id}/editar", response_model=VersaoMinutaPublicSchema)
@limiter.limit(LIMITE_ELABORACAO_GERAR)
async def editar_minuta(
    request: Request,
    elaboracao_id: UUID,
    body: EditarMinutaSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> VersaoMinutaPublicSchema:
    try:
        resultado = await elaboracao_service.registrar_edicao(
            db,
            current_user.id,
            elaboracao_id,
            instrucao=body.instrucao,
            trecho_selecionado=body.trecho_selecionado,
        )
    except elaboracao_service.SemVersaoAnteriorError as exc:
        raise _SEM_VERSAO_ANTERIOR from exc
    except elaboracao_service.VersaoIlegivelError as exc:
        raise _VERSAO_ILEGIVEL from exc
    except LLMLimiteAtingidoError as exc:
        raise _COTA_MODELO from exc
    except LLMProviderNaoConfiguradoError as exc:
        raise _MODELO_NAO_CONFIGURADO from exc
    if resultado is None:
        raise _NAO_ENCONTRADA
    return resultado


@router.post("/{elaboracao_id}/estilo", response_model=ElaboracaoPublicSchema)
@limiter.limit(LIMITE_ELABORACAO_GERAR)
async def definir_estilo(
    request: Request,
    elaboracao_id: UUID,
    body: EstiloTextoSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> ElaboracaoPublicSchema:
    try:
        resultado = await elaboracao_service.definir_estilo_por_texto(
            db, current_user.id, elaboracao_id, texto=body.texto
        )
    except LLMLimiteAtingidoError as exc:
        raise _COTA_MODELO from exc
    except LLMProviderNaoConfiguradoError as exc:
        raise _MODELO_NAO_CONFIGURADO from exc
    if resultado is None:
        raise _NAO_ENCONTRADA
    return resultado


@router.get("/{elaboracao_id}/versoes", response_model=list[VersaoMinutaPublicSchema])
async def listar_versoes(
    elaboracao_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[VersaoMinutaPublicSchema]:
    resultado = await elaboracao_service.listar_versoes(db, current_user.id, elaboracao_id)
    if resultado is None:
        raise _NAO_ENCONTRADA
    return resultado
