from core.database.models import Organization, User, OrganizationMember
"""
Repositories SQLAlchemy Auth — Sprint 21.

Implémentations concrètes des ports du domaine Auth.
Ces classes sont la seule couche autorisée à toucher SQLAlchemy pour le module auth.

Chaque repository implémente le Protocol correspondant défini dans auth/domain/ports.py.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.auth.domain.entities import (
    InvitationEntity,
    MembershipEntity,
    OrganizationEntity,
    UserEntity,
)
from modules.auth.domain.value_objects import Email, HashedPassword, OrgSlug
from .persistence.models import (
    Invitation,
    InvitationStatus,
    Organization,
    OrganizationMember,
    User,
    UserRole,
)

from .mappers import (
    invitation_to_entity,
    membership_to_entity,
    org_to_entity,
    user_to_entity,
)


class SQLAlchemyUserRepository:
    """Repository utilisateurs — implémente IUserRepository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        result = await self._db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.organizations).selectinload(
                    OrganizationMember.organization
                )
            )
        )
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> Optional[UserEntity]:
        result = await self._db.execute(
            select(User)
            .where(func.lower(User.email) == email.value.lower())
            .options(
                selectinload(User.organizations).selectinload(
                    OrganizationMember.organization
                )
            )
        )
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model else None

    async def get_by_google_id(self, google_id: str) -> Optional[UserEntity]:
        result = await self._db.execute(
            select(User).where(User.google_id == google_id)
        )
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model else None

    async def get_by_verification_token(self, token: str) -> Optional[User]:
        """Retourne le modèle User brut correspondant au token."""
        result = await self._db.execute(
            select(User).where(User.verification_token == token)
        )
        return result.scalar_one_or_none()

    async def get_model_by_id(self, user_id: UUID) -> Optional[User]:
        """Retourne le modèle SQLAlchemy brut avec relations fraîches."""
        # On force le rechargement depuis la DB même si déjà en session
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.organizations).selectinload(
                    OrganizationMember.organization
                )
            )
            .execution_options(populate_existing=True)
        )
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()
        return model

    async def get_model_by_email(self, email: str) -> Optional[User]:
        """Retourne le modèle SQLAlchemy brut (usage interne infrastructure)."""
        result = await self._db.execute(
            select(User)
            .where(func.lower(User.email) == email.strip().lower())
            .options(
                selectinload(User.organizations).selectinload(
                    OrganizationMember.organization
                )
            )
        )
        return result.scalar_one_or_none()

    async def save(
        self, user: User
    ) -> UserEntity:
        """Persiste un modèle User (add + flush) et retourne l'entité domaine."""
        self._db.add(user)
        await self._db.flush()
        return user_to_entity(user)

    async def update(self, user: UserEntity) -> UserEntity:
        model = await self.get_model_by_id(user.id)
        if not model:
            raise ValueError(f"User {user.id} introuvable")
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.is_active = user.is_active
        model.current_organization_id = user.current_organization_id
        model.preferences = user.preferences
        await self._db.flush()
        return user_to_entity(model)


class SQLAlchemyOrganizationRepository:
    """Repository organisations — implémente IOrganizationRepository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, org_id: UUID) -> Optional[OrganizationEntity]:
        result = await self._db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        model = result.scalar_one_or_none()
        return org_to_entity(model) if model else None

    async def get_by_slug(self, slug: OrgSlug) -> Optional[OrganizationEntity]:
        result = await self._db.execute(
            select(Organization).where(Organization.slug == slug.value)
        )
        model = result.scalar_one_or_none()
        return org_to_entity(model) if model else None

    async def save(self, org: Organization) -> OrganizationEntity:
        """Persiste un modèle Organization et retourne l'entité domaine."""
        self._db.add(org)
        await self._db.flush()
        return org_to_entity(org)

    async def list_for_user(self, user_id: UUID) -> list[OrganizationEntity]:
        result = await self._db.execute(
            select(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
        )
        return [org_to_entity(m) for m in result.scalars().all()]


class SQLAlchemyMembershipRepository:
    """Repository memberships — implémente IMembershipRepository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, org_id: UUID, user_id: UUID) -> Optional[MembershipEntity]:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return membership_to_entity(model) if model else None

    async def save(self, model: OrganizationMember) -> MembershipEntity:
        self._db.add(model)
        await self._db.flush()
        return membership_to_entity(model)

    async def list_for_user(self, user_id: UUID) -> list[MembershipEntity]:
        result = await self._db.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == user_id)
        )
        return [membership_to_entity(m) for m in result.scalars().all()]

    async def list_for_org(self, org_id: UUID) -> list[MembershipEntity]:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id
            )
        )
        return [membership_to_entity(m) for m in result.scalars().all()]

    async def list_models_for_org(self, org_id: UUID) -> list[OrganizationMember]:
        """Retourne les modèles SQLAlchemy avec la relation user chargée (pour les resolvers GraphQL)."""
        result = await self._db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
            .options(selectinload(OrganizationMember.user))
        )
        return list(result.scalars().all())

    async def delete(self, org_id: UUID, user_id: UUID) -> None:
        await self._db.execute(
            delete(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )

    async def update_role(
        self, org_id: UUID, user_id: UUID, role: UserRole
    ) -> Optional[MembershipEntity]:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            model.role = role
            await self._db.flush()
            return membership_to_entity(model)
        return None

    async def update_permissions(
        self, org_id: UUID, user_id: UUID, permissions: dict
    ) -> Optional[MembershipEntity]:
        result = await self._db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model:
            model.permissions = permissions
            await self._db.flush()
            return membership_to_entity(model)
        return None


class SQLAlchemyInvitationRepository:
    """Repository invitations — implémente IInvitationRepository."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_code(self, code: str) -> Optional[InvitationEntity]:
        result = await self._db.execute(
            select(Invitation).where(Invitation.code == code)
        )
        model = result.scalar_one_or_none()
        return invitation_to_entity(model) if model else None

    async def get_model_by_code(self, code: str) -> Optional[Invitation]:
        result = await self._db.execute(
            select(Invitation).where(Invitation.code == code)
        )
        return result.scalar_one_or_none()

    async def save(self, model: Invitation) -> InvitationEntity:
        self._db.add(model)
        await self._db.flush()
        return invitation_to_entity(model)

    async def update(self, entity: InvitationEntity) -> InvitationEntity:
        result = await self._db.execute(
            select(Invitation).where(Invitation.id == entity.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Invitation {entity.id} introuvable")
        from modules.auth.infrastructure.models import InvitationStatus as ModelStatus
        status_map = {
            InvitationStatus.PENDING: ModelStatus.PENDING,
            InvitationStatus.ACCEPTED: ModelStatus.ACCEPTED,
            InvitationStatus.EXPIRED: ModelStatus.EXPIRED,
        }
        model.status = status_map.get(entity.status, ModelStatus.PENDING)
        await self._db.flush()
        return invitation_to_entity(model)

    async def list_for_org(self, org_id: UUID) -> list[InvitationEntity]:
        """Liste toutes les invitations d'une organisation."""
        result = await self._db.execute(
            select(Invitation).where(Invitation.organization_id == org_id)
        )
        return [invitation_to_entity(m) for m in result.scalars().all()]

    async def get_pending_invitation(self, email: str, org_id: UUID) -> Optional[InvitationEntity]:
        result = await self._db.execute(
            select(Invitation).where(
                func.lower(Invitation.email) == email.strip().lower(),
                Invitation.organization_id == org_id,
                Invitation.status == InvitationStatus.PENDING,
            )
        )
        model = result.scalar_one_or_none()
        return invitation_to_entity(model) if model else None

    async def delete_invitation(self, invitation_id: UUID) -> None:
        await self._db.execute(
            delete(Invitation).where(Invitation.id == invitation_id)
        )
        await self._db.flush()

    async def delete_by_id(self, invitation_id: UUID) -> bool:
        result = await self._db.execute(
            select(Invitation).where(Invitation.id == invitation_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._db.delete(model)
            await self._db.flush()
            return True
        return False
