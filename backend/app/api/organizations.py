"""Rotas de organizações, membros e convites.

`user_id` vem só do JWT. `organization_id` no path é conferido contra
`organization_members` antes de qualquer leitura ou escrita.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.permissions import ACOES_POR_PAPEL, CurrentOrgMember, require_role
from app.core.rate_limit import LIMITE_ACEITE_CONVITE, limiter
from app.models.organization import Organization, OrganizationMember
from app.schemas.organization import (
    InviteAcceptedSchema,
    InviteCreateSchema,
    InvitePendingSchema,
    InvitePreviewSchema,
    InviteReceivedSchema,
    MemberPublicSchema,
    MemberRoleUpdateSchema,
    OrganizationCreateSchema,
    OrganizationDetailSchema,
    OrganizationMineSchema,
    OrganizationUpdateSchema,
)
from app.services import organizations as orgs

router = APIRouter(prefix="/organizations", tags=["organizations"])

MembroGestor = Annotated[
    OrganizationMember, Depends(require_role(ACOES_POR_PAPEL["configurar"]))
]
MembroDono = Annotated[
    OrganizationMember, Depends(require_role(ACOES_POR_PAPEL["excluir_organizacao"]))
]


def _detalhe(org: Organization, role: str) -> OrganizationDetailSchema:
    return OrganizationDetailSchema(
        id=org.id,
        name=org.name,
        slug=org.slug,
        role=role,
        created_at=org.created_at,
    )


def _aceite(org: Organization, role: str) -> InviteAcceptedSchema:
    return InviteAcceptedSchema(
        organization_id=org.id,
        name=org.name,
        slug=org.slug,
        role=role,
    )


async def _org_do_membro(db: DbSession, member: OrganizationMember) -> Organization:
    org = await db.get(Organization, member.organization_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organização não encontrada")
    return org


@router.get("", response_model=list[OrganizationMineSchema])
async def listar_organizacoes(
    current_user: CurrentUser,
    db: DbSession,
) -> list[OrganizationMineSchema]:
    linhas = await orgs.listar_minhas(db, current_user.id)
    return [
        OrganizationMineSchema(id=org.id, name=org.name, slug=org.slug, role=role)
        for org, role in linhas
    ]


@router.post("", response_model=OrganizationDetailSchema, status_code=status.HTTP_201_CREATED)
async def criar_organizacao(
    dados: OrganizationCreateSchema,
    current_user: CurrentUser,
    db: DbSession,
) -> OrganizationDetailSchema:
    org, membro = await orgs.criar_organizacao(db, current_user, dados.name)
    return _detalhe(org, membro.role)


@router.get("/invites/received", response_model=list[InviteReceivedSchema])
async def listar_convites_recebidos(
    current_user: CurrentUser,
    db: DbSession,
) -> list[InviteReceivedSchema]:
    linhas = await orgs.listar_convites_recebidos(db, current_user.email)
    return [
        InviteReceivedSchema(
            id=convite.id,
            organization_name=org.name,
            role=convite.role,
            expires_at=convite.expires_at,
            created_at=convite.created_at,
        )
        for convite, org in linhas
    ]


@router.post("/invites/received/{invite_id}/accept", response_model=InviteAcceptedSchema)
@limiter.limit(LIMITE_ACEITE_CONVITE)
async def aceitar_convite_recebido(
    request: Request,
    invite_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> InviteAcceptedSchema:
    org, membro = await orgs.aceitar_recebido(db, current_user, invite_id)
    return _aceite(org, membro.role)


@router.post("/invites/received/{invite_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(LIMITE_ACEITE_CONVITE)
async def recusar_convite_recebido(
    request: Request,
    invite_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    await orgs.recusar_recebido(db, current_user, invite_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/invites/{token}", response_model=InvitePreviewSchema)
@limiter.limit(LIMITE_ACEITE_CONVITE)
async def preview_convite(request: Request, token: str, db: DbSession) -> InvitePreviewSchema:
    convite, org = await orgs.preview_por_token(db, token)
    return InvitePreviewSchema(
        organization_name=org.name,
        role=convite.role,
        email=convite.email,
        expires_at=convite.expires_at,
    )


@router.post("/invites/{token}/accept", response_model=InviteAcceptedSchema)
@limiter.limit(LIMITE_ACEITE_CONVITE)
async def aceitar_convite_por_token(
    request: Request,
    token: str,
    current_user: CurrentUser,
    db: DbSession,
) -> InviteAcceptedSchema:
    org, membro = await orgs.aceitar_por_token(db, current_user, token)
    return _aceite(org, membro.role)


@router.post("/invites/{token}/decline", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(LIMITE_ACEITE_CONVITE)
async def recusar_convite_por_token(
    request: Request,
    token: str,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    await orgs.recusar_por_token(db, current_user, token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{org_id}", response_model=OrganizationDetailSchema)
async def detalhe_organizacao(
    org_id: UUID,
    member: CurrentOrgMember,
    db: DbSession,
) -> OrganizationDetailSchema:
    del org_id
    org = await _org_do_membro(db, member)
    return _detalhe(org, member.role)


@router.patch("/{org_id}", response_model=OrganizationDetailSchema)
async def renomear_organizacao(
    org_id: UUID,
    dados: OrganizationUpdateSchema,
    member: MembroGestor,
    db: DbSession,
) -> OrganizationDetailSchema:
    org = await orgs.renomear(db, org_id, dados.name)
    return _detalhe(org, member.role)


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def excluir_organizacao(
    org_id: UUID,
    member: MembroDono,
    db: DbSession,
) -> Response:
    del member
    await orgs.excluir(db, org_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{org_id}/members", response_model=list[MemberPublicSchema])
async def listar_membros(
    org_id: UUID,
    member: CurrentOrgMember,
    db: DbSession,
) -> list[MemberPublicSchema]:
    del org_id
    linhas = await orgs.membros_publicos(db, member.organization_id)
    return [
        MemberPublicSchema(
            id=membro.id,
            name=usuario.name,
            email=usuario.email,
            role=membro.role,
            joined_at=membro.joined_at,
        )
        for membro, usuario in linhas
    ]


@router.patch("/{org_id}/members/{member_id}", response_model=MemberPublicSchema)
async def alterar_papel(
    org_id: UUID,
    member_id: UUID,
    dados: MemberRoleUpdateSchema,
    member: MembroGestor,
    db: DbSession,
) -> MemberPublicSchema:
    del member
    alvo, usuario = await orgs.alterar_papel(db, org_id, member_id, dados.role)
    return MemberPublicSchema(
        id=alvo.id,
        name=usuario.name,
        email=usuario.email,
        role=alvo.role,
        joined_at=alvo.joined_at,
    )


@router.delete("/{org_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_membro(
    org_id: UUID,
    member_id: UUID,
    member: CurrentOrgMember,
    db: DbSession,
) -> Response:
    await orgs.remover_membro(db, org_id, member, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{org_id}/members/{member_id}/transfer-ownership",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def transferir_ownership(
    org_id: UUID,
    member_id: UUID,
    member: MembroDono,
    db: DbSession,
) -> Response:
    await orgs.transferir_ownership(db, org_id, member, member_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{org_id}/invites", response_model=list[InvitePendingSchema])
async def listar_convites(
    org_id: UUID,
    member: MembroGestor,
    db: DbSession,
) -> list[InvitePendingSchema]:
    del org_id
    convites = await orgs.listar_convites_pendentes(db, member.organization_id)
    return [
        InvitePendingSchema(
            id=convite.id,
            email=convite.email,
            role=convite.role,
            expires_at=convite.expires_at,
            created_at=convite.created_at,
        )
        for convite in convites
    ]


@router.post(
    "/{org_id}/invites",
    response_model=InvitePendingSchema,
    status_code=status.HTTP_201_CREATED,
)
async def convidar(
    org_id: UUID,
    dados: InviteCreateSchema,
    member: MembroGestor,
    db: DbSession,
) -> InvitePendingSchema:
    del org_id
    org = await _org_do_membro(db, member)
    convite = await orgs.criar_ou_renovar_convite(
        db,
        org,
        member.user_id,
        dados.email,
        dados.role,
    )
    return InvitePendingSchema(
        id=convite.id,
        email=convite.email,
        role=convite.role,
        expires_at=convite.expires_at,
        created_at=convite.created_at,
    )


@router.delete("/{org_id}/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar_convite(
    org_id: UUID,
    invite_id: UUID,
    member: MembroGestor,
    db: DbSession,
) -> Response:
    del member
    await orgs.cancelar_convite(db, org_id, invite_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
