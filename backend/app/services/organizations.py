"""Regras de organização: slug, convite com token hasheado e membership.

O token cru só existe na memória até o log de development. A notificação
in-app nunca leva o token.
"""

import logging
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_token
from app.models.notification import NOTIFICATION_TIPO_CONVITE_ORG, Notification
from app.models.organization import (
    ROLE_ADMIN,
    ROLE_OWNER,
    ROLES_CONVIDAVEIS,
    ROTULO_PAPEL,
    Organization,
    OrganizationInvite,
    OrganizationMember,
)
from app.models.user import User

logger = logging.getLogger(__name__)

CONVITE_VALIDADE = timedelta(days=7)
SLUG_MAX = 80
_SLUG_BASE_MAX = 60
_NAO_SLUG = re.compile(r"[^a-z0-9]+")
_UUID_CONVITE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

_SEM_PERMISSAO = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Sem permissão para esta ação",
)


def slugificar(nome: str) -> str:
    """Nome visível → slug estável (minúsculo, sem acento, hífens)."""
    normalizado = unicodedata.normalize("NFKD", nome)
    sem_acento = "".join(c for c in normalizado if not unicodedata.combining(c))
    slug = _NAO_SLUG.sub("-", sem_acento.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:SLUG_MAX] or "organizacao"


def novo_token_convite() -> tuple[str, str]:
    """UUID v4 cru (só para o link) e o hash que vai para o banco."""
    token = str(uuid4())
    return token, hash_token(token)


def registrar_link_convite(invited_by: UUID, token: str) -> None:
    """Em development, o link vai para o log. Fora disso, o token não aparece."""
    settings = get_settings()
    if settings.is_development:
        link = f"{settings.frontend_url}/convite/{token}"
        logger.warning(
            "Link de convite gerado para user_id=%s: %s",
            invited_by,
            link,
        )
        return
    logger.info("Convite de organização gerado para user_id=%s", invited_by)


async def gerar_slug_unico(db: AsyncSession, nome: str) -> str:
    base = slugificar(nome)[:_SLUG_BASE_MAX].strip("-") or "organizacao"
    candidato = base
    sufixo = 2
    while await db.scalar(select(Organization.id).where(Organization.slug == candidato)):
        candidato = f"{base}-{sufixo}"
        sufixo += 1
        if sufixo > 1000:
            candidato = f"{base}-{uuid4().hex[:6]}"
            break
    return candidato[:SLUG_MAX]


async def criar_organizacao(
    db: AsyncSession, user: User, nome: str
) -> tuple[Organization, OrganizationMember]:
    agora = datetime.now(UTC)
    org = Organization(
        name=nome,
        slug=await gerar_slug_unico(db, nome),
        created_by=user.id,
    )
    db.add(org)
    await db.flush()
    membro = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=ROLE_OWNER,
        invited_by=user.id,
        joined_at=agora,
    )
    db.add(membro)
    await db.commit()
    return org, membro


async def listar_minhas(db: AsyncSession, user_id: UUID) -> list[tuple[Organization, str]]:
    linhas = (
        await db.execute(
            select(Organization, OrganizationMember.role)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.name)
        )
    ).all()
    return [(org, role) for org, role in linhas]


async def renomear(db: AsyncSession, org_id: UUID, nome: str) -> Organization:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organização não encontrada")
    org.name = nome
    await db.commit()
    return org


async def excluir(db: AsyncSession, org_id: UUID) -> None:
    org = await db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organização não encontrada")
    await db.delete(org)
    await db.commit()


async def membros_publicos(db: AsyncSession, org_id: UUID) -> list[tuple[OrganizationMember, User]]:
    linhas = (
        await db.execute(
            select(OrganizationMember, User)
            .join(User, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == org_id)
            .order_by(OrganizationMember.joined_at, User.name)
        )
    ).all()
    return [(membro, usuario) for membro, usuario in linhas]


async def alterar_papel(
    db: AsyncSession, org_id: UUID, member_id: UUID, role: str
) -> tuple[OrganizationMember, User]:
    if role not in ROLES_CONVIDAVEIS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Papel inválido",
        )
    alvo, usuario = await _membro_da_org(db, org_id, member_id)
    if alvo.role == ROLE_OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível alterar o papel do Owner",
        )
    alvo.role = role
    await db.commit()
    return alvo, usuario


async def remover_membro(
    db: AsyncSession, org_id: UUID, actor: OrganizationMember, member_id: UUID
) -> None:
    alvo, _usuario = await _membro_da_org(db, org_id, member_id)
    if alvo.role == ROLE_OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível remover o Owner",
        )
    if alvo.user_id != actor.user_id and actor.role not in (ROLE_OWNER, ROLE_ADMIN):
        raise _SEM_PERMISSAO
    await db.delete(alvo)
    await db.commit()


async def transferir_ownership(
    db: AsyncSession, org_id: UUID, actor: OrganizationMember, member_id: UUID
) -> None:
    alvo, _usuario = await _membro_da_org(db, org_id, member_id)
    if alvo.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Escolha outro membro para receber a organização",
        )
    alvo.role = ROLE_OWNER
    actor.role = ROLE_ADMIN
    await db.commit()


async def criar_ou_renovar_convite(
    db: AsyncSession,
    org: Organization,
    invited_by: UUID,
    email: str,
    role: str,
) -> OrganizationInvite:
    if role not in ROLES_CONVIDAVEIS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Papel de convite inválido",
        )
    email_normalizado = email.lower()
    usuario = await db.scalar(select(User).where(User.email == email_normalizado))
    if usuario is not None:
        ja_membro = await db.scalar(
            select(OrganizationMember.id).where(
                OrganizationMember.organization_id == org.id,
                OrganizationMember.user_id == usuario.id,
            )
        )
        if ja_membro is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já é membro da organização",
            )

    agora = datetime.now(UTC)
    token, token_hash = novo_token_convite()
    convite = await db.scalar(
        select(OrganizationInvite).where(
            OrganizationInvite.organization_id == org.id,
            OrganizationInvite.email == email_normalizado,
            OrganizationInvite.accepted_at.is_(None),
            OrganizationInvite.revoked_at.is_(None),
        )
    )
    if convite is None:
        convite = OrganizationInvite(
            organization_id=org.id,
            email=email_normalizado,
            role=role,
            invited_by=invited_by,
            token_hash=token_hash,
            expires_at=agora + CONVITE_VALIDADE,
        )
        db.add(convite)
    else:
        convite.role = role
        convite.invited_by = invited_by
        convite.token_hash = token_hash
        convite.expires_at = agora + CONVITE_VALIDADE

    if usuario is not None:
        db.add(
            Notification(
                user_id=usuario.id,
                tipo=NOTIFICATION_TIPO_CONVITE_ORG,
                titulo="Convite para organização",
                message=(
                    f"Você foi convidado para {org.name} como {ROTULO_PAPEL[role]}."
                ),
            )
        )

    await db.commit()
    registrar_link_convite(invited_by, token)
    return convite


async def listar_convites_pendentes(db: AsyncSession, org_id: UUID) -> list[OrganizationInvite]:
    agora = datetime.now(UTC)
    return list(
        (
            await db.scalars(
                select(OrganizationInvite)
                .where(
                    OrganizationInvite.organization_id == org_id,
                    OrganizationInvite.accepted_at.is_(None),
                    OrganizationInvite.revoked_at.is_(None),
                    OrganizationInvite.expires_at > agora,
                )
                .order_by(OrganizationInvite.created_at)
            )
        ).all()
    )


async def cancelar_convite(db: AsyncSession, org_id: UUID, invite_id: UUID) -> None:
    convite = await _convite_aberto_da_org(db, org_id, invite_id)
    convite.revoked_at = datetime.now(UTC)
    await db.commit()


async def listar_convites_recebidos(
    db: AsyncSession, email: str
) -> list[tuple[OrganizationInvite, Organization]]:
    agora = datetime.now(UTC)
    linhas = (
        await db.execute(
            select(OrganizationInvite, Organization)
            .join(Organization, Organization.id == OrganizationInvite.organization_id)
            .where(
                OrganizationInvite.email == email.lower(),
                OrganizationInvite.accepted_at.is_(None),
                OrganizationInvite.revoked_at.is_(None),
                OrganizationInvite.expires_at > agora,
            )
            .order_by(OrganizationInvite.created_at)
        )
    ).all()
    return [(convite, org) for convite, org in linhas]


async def aceitar_recebido(
    db: AsyncSession, user: User, invite_id: UUID
) -> tuple[Organization, OrganizationMember]:
    convite = await _convite_recebido(db, user, invite_id)
    return await _aceitar(db, user, convite)


async def recusar_recebido(db: AsyncSession, user: User, invite_id: UUID) -> None:
    convite = await _convite_recebido(db, user, invite_id)
    await _recusar(db, convite)


async def preview_por_token(db: AsyncSession, token: str) -> tuple[OrganizationInvite, Organization]:
    convite = await _convite_por_token(db, token)
    _garantir_utilizavel(convite)
    org = await db.get(Organization, convite.organization_id)
    if org is None:
        raise _convite_invalido()
    return convite, org


async def aceitar_por_token(
    db: AsyncSession, user: User, token: str
) -> tuple[Organization, OrganizationMember]:
    convite = await _convite_por_token(db, token)
    _garantir_utilizavel(convite)
    _garantir_email(convite, user)
    return await _aceitar(db, user, convite)


async def recusar_por_token(db: AsyncSession, user: User, token: str) -> None:
    convite = await _convite_por_token(db, token)
    _garantir_utilizavel(convite)
    _garantir_email(convite, user)
    await _recusar(db, convite)


async def _membro_da_org(
    db: AsyncSession, org_id: UUID, member_id: UUID
) -> tuple[OrganizationMember, User]:
    linha = (
        await db.execute(
            select(OrganizationMember, User)
            .join(User, User.id == OrganizationMember.user_id)
            .where(
                OrganizationMember.id == member_id,
                OrganizationMember.organization_id == org_id,
            )
        )
    ).one_or_none()
    if linha is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro não encontrado")
    return linha


async def _convite_aberto_da_org(
    db: AsyncSession, org_id: UUID, invite_id: UUID
) -> OrganizationInvite:
    convite = await db.scalar(
        select(OrganizationInvite).where(
            OrganizationInvite.id == invite_id,
            OrganizationInvite.organization_id == org_id,
            OrganizationInvite.accepted_at.is_(None),
            OrganizationInvite.revoked_at.is_(None),
        )
    )
    if convite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite não encontrado")
    return convite


async def _convite_recebido(db: AsyncSession, user: User, invite_id: UUID) -> OrganizationInvite:
    agora = datetime.now(UTC)
    convite = await db.scalar(
        select(OrganizationInvite).where(
            OrganizationInvite.id == invite_id,
            OrganizationInvite.email == user.email.lower(),
            OrganizationInvite.accepted_at.is_(None),
            OrganizationInvite.revoked_at.is_(None),
            OrganizationInvite.expires_at > agora,
        )
    )
    if convite is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite não encontrado")
    return convite


async def _convite_por_token(db: AsyncSession, token: str) -> OrganizationInvite:
    if not _UUID_CONVITE.match(token):
        raise _convite_invalido()
    convite = await db.scalar(
        select(OrganizationInvite).where(OrganizationInvite.token_hash == hash_token(token))
    )
    if convite is None:
        raise _convite_invalido()
    return convite


def _garantir_utilizavel(convite: OrganizationInvite) -> None:
    if convite.accepted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Convite já utilizado")
    if convite.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Convite cancelado")
    if convite.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Convite expirado")


def _garantir_email(convite: OrganizationInvite, user: User) -> None:
    if convite.email != user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este convite não é para sua conta",
        )


async def _aceitar(
    db: AsyncSession, user: User, convite: OrganizationInvite
) -> tuple[Organization, OrganizationMember]:
    ja_membro = await db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == convite.organization_id,
            OrganizationMember.user_id == user.id,
        )
    )
    if ja_membro is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já é membro da organização",
        )
    org = await db.get(Organization, convite.organization_id)
    if org is None:
        raise _convite_invalido()
    agora = datetime.now(UTC)
    membro = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=convite.role,
        invited_by=convite.invited_by,
        joined_at=agora,
    )
    convite.accepted_at = agora
    db.add(membro)
    await db.commit()
    return org, membro


async def _recusar(db: AsyncSession, convite: OrganizationInvite) -> None:
    convite.revoked_at = datetime.now(UTC)
    await db.commit()


def _convite_invalido() -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Convite inválido")
