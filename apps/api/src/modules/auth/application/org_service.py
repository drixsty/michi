from core.database.models import Organization, User, OrganizationMember
"""
Application OrgService (DDD) — Sprint 21.

Service applicatif de gestion des organisations.
Extrait la logique de schema.py (create_organization, switch_organization)
et de invitation_service.py.

Aucune dépendance SQLAlchemy directe — pur Python métier.
"""

import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from modules.auth.domain.entities import InvitationEntity, MembershipEntity, OrganizationEntity
from modules.auth.domain.value_objects import JwtToken
from modules.auth.infrastructure.repositories import (
    SQLAlchemyInvitationRepository,
    SQLAlchemyMembershipRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyUserRepository,
)
from modules.auth.domain.ports import ITokenService
from modules.auth.infrastructure.models import (
    Invitation,
    InvitationStatus,
    Organization,
    OrganizationMember,
    UserRole,
)
from core.exceptions import ErrorCode, MichiException


@dataclass
class OrgCreationResult:
    """Résultat de la création d'organisation."""
    token: JwtToken
    user_model: object
    org_model: Organization


class ApplicationOrgService:
    """
    Service de gestion des organisations — couche Application (DDD hexagonal).

    Encapsule toute la logique org actuellement dans schema.py (create_organization,
    switch_organization) et invitation_service.py.
    """

    def __init__(
        self,
        user_repo: SQLAlchemyUserRepository,
        org_repo: SQLAlchemyOrganizationRepository,
        membership_repo: SQLAlchemyMembershipRepository,
        invitation_repo: SQLAlchemyInvitationRepository,
        token_service: ITokenService,
        billing_service=None,
    ) -> None:
        self._users = user_repo
        self._orgs = org_repo
        self._memberships = membership_repo
        self._invitations = invitation_repo
        self._tokens = token_service
        self._billing = billing_service

    async def create_organization(
        self,
        user_id: uuid.UUID,
        name: str,
        plan: str = "BASIC",
        email: Optional[str] = None
    ) -> OrgCreationResult:
        """
        Crée une organisation...
        """
        # Primary lookup by ID
        user_model = await self._users.get_model_by_id(user_id)
        
        # Sprint 22 Extension: Primary fallback - retry by ID
        if not user_model:
            import asyncio
            await asyncio.sleep(1.0)
            user_model = await self._users.get_model_by_id(user_id)
            
        # Sprint 22 Extension: Secondary fallback - lookup by Email
        if not user_model and email:
            print(f">>> [DEBUG] USER ID {user_id} NOT FOUND, TRYING EMAIL FALLBACK: {email} <<<")
            user_model = await self._users.get_model_by_email(email)

        if not user_model:
            raise ValueError(f"User {user_id} / {email} introuvable")

        slug = f"org-{uuid.uuid4().hex[:8]}"
        org_model = Organization(name=name, slug=slug, plan=plan.upper())
        await self._orgs.save(org_model)

        member = OrganizationMember(
            user_id=user_id,
            organization_id=org_model.id,
            role=UserRole.ADMIN,
        )
        await self._memberships.save(member)

        user_model.current_organization_id = org_model.id
        
        if self._billing:
            stripe_id = await self._billing.create_customer(
                name=org_model.name,
                email=user_model.email,
                org_id=str(org_model.id),
            )
            if stripe_id:
                org_model.stripe_customer_id = stripe_id

        # Commit global pour assurer que GET_ME (requête suivante) voit l'organisation
        await self._users._db.commit()

        # Sprint 22 Final Hardening: Refresh relationships to break the redirect loop
        # ensuring UserType.from_db and secondary GET_ME see the new memberships
        await self._users._db.refresh(user_model, ["organizations"])

        token = self._tokens.create_access_token(
            user_id=user_model.id,
            org_id=org_model.id,
            email=user_model.email,
        )

        return OrgCreationResult(token=token, user_model=user_model, org_model=org_model)

    async def switch_organization(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> tuple[JwtToken, object]:
        """
        Bascule le contexte organisation d'un utilisateur et retourne un token rafraîchi.

        Returns:
            Tuple (token, user_model).

        Raises:
            ValueError: si l'utilisateur n'est pas trouvé.
        """
        user_model = await self._users.get_model_by_id(user_id)
        if not user_model:
            raise ValueError(f"User {user_id} introuvable")

        user_model.current_organization_id = organization_id
        await self._users._db.flush()

        token = self._tokens.create_access_token(
            user_id=user_model.id,
            org_id=organization_id,
            email=user_model.email,
        )
        return token, user_model

    async def create_invitation(
        self,
        email: str,
        organization_id: uuid.UUID,
        role: UserRole,
        invited_by_id: uuid.UUID,
    ) -> Invitation:
        """
        Crée une invitation collaborateur (7 jours d'expiration).

        Raises:
            MichiException(ALREADY_MEMBER): membre actif.
            MichiException(INVITATION_ALREADY_PENDING): invitation en attente non expirée.
        """
        email = email.strip().lower()

        # 1. Vérifier membre existant via repository
        existing_user = await self._users.get_model_by_email(email)
        if existing_user:
            memberships = await self._memberships.list_for_user(existing_user.id)
            if any(str(m.organization_id) == str(organization_id) for m in memberships):
                raise MichiException(
                    message=f"L'utilisateur {email} est déjà membre.",
                    code=ErrorCode.ALREADY_MEMBER,
                )

        # 2. Vérifier invitation en attente via repository
        pending = await self._invitations.get_pending_invitation(email, organization_id)
        if pending:
            if pending.expires_at < datetime.utcnow():
                await self._invitations.delete_invitation(pending.id)
            else:
                raise MichiException(
                    message=f"Une invitation est déjà en attente pour {email}.",
                    code=ErrorCode.INVITATION_ALREADY_PENDING,
                )

        # 3. Création
        code = secrets.token_urlsafe(16)
        invitation = Invitation(
            email=email,
            organization_id=organization_id,
            role=role,
            code=code,
            invited_by_id=invited_by_id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            status=InvitationStatus.PENDING,
        )
        await self._invitations.save(invitation)
        return invitation

    async def accept_invitation(self, code: str, user_id: uuid.UUID) -> bool:
        """Valide un code d'invitation et ajoute l'utilisateur à l'organisation."""
        invitation = await self._invitations.get_model_by_code(code)
        if not invitation or invitation.status != InvitationStatus.PENDING:
            return False

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED
            await self._users._db.flush()
            return False

        user_model = await self._users.get_model_by_id(user_id)
        if not user_model:
            return False

        # Vérification stricte : l'email du compte doit correspondre à l'email invité
        if user_model.email.lower() != invitation.email.lower():
            raise MichiException(
                message="Impossible d'accepter cette invitation avec ce compte. Veuillez vous connecter avec l'adresse e-mail qui a reçu l'invitation.",
                code=ErrorCode.FORBIDDEN
            )

        member = OrganizationMember(
            user_id=user_id,
            organization_id=invitation.organization_id,
            role=invitation.role,
        )
        await self._memberships.save(member)
        invitation.status = InvitationStatus.ACCEPTED

        user_model.current_organization_id = invitation.organization_id

        await self._users._db.flush()
        return True

    async def get_members(self, org_id: uuid.UUID) -> list[MembershipEntity]:
        """Liste les membres d'une organisation."""
        return await self._memberships.list_for_org(org_id)

    async def get_members_with_users(self, org_id: uuid.UUID) -> list:
        """Liste les membres avec la relation user chargée — pour les resolvers GraphQL."""
        return await self._memberships.list_models_for_org(org_id)

    async def get_pending_invitations(self, org_id: uuid.UUID) -> list[InvitationEntity]:
        """Liste les invitations en attente d'une organisation."""
        all_invitations = await self._invitations.list_for_org(org_id)
        return [i for i in all_invitations if i.status == InvitationStatus.PENDING and i.expires_at > datetime.utcnow()]

    async def get_current_org(self, org_id: uuid.UUID) -> Optional[OrganizationEntity]:
        """
        Récupère les détails d'une organisation de manière sécurisée.
        """
        from loguru import logger
        try:
            org = await self._orgs.get_by_id(org_id)
            if not org:
                logger.warning(f"Organization {org_id} not found during retrieval")
                return None
            return org
        except Exception as e:
            logger.error(f"Error retrieving organization {org_id}: {str(e)}")
            return None

    async def update_organization(self, org_id: uuid.UUID, **kwargs) -> Optional[OrganizationEntity]:
        """Met à jour une organisation."""
        org_model = await self._orgs._db.get(Organization, org_id) # Direct access for simplicity in update
        if not org_model:
            return None
        
        from loguru import logger
        logger.info(f"[Service] Updating Org {org_id}: name={kwargs.get('name')}, completed={kwargs.get('onboarding_completed')}, step={kwargs.get('onboarding_step')}")

        if kwargs.get("name") is not None:
            org_model.name = str(kwargs["name"])
        if kwargs.get("settings") is not None:
            org_model.settings = kwargs["settings"]
        if kwargs.get("onboarding_completed") is not None:
            val = bool(kwargs["onboarding_completed"])
            org_model.onboarding_completed = val
            logger.warning(f"[Service] Set onboarding_completed to {val} for Org {org_id}")
            
            # Si l'onboarding est terminé, on s'assure que l'utilisateur est bien sur cette org
            if val:
                from modules.auth.infrastructure.models import OrganizationMember, User
                from sqlalchemy import select
                # On cherche le propriétaire (ou l'utilisateur courant)
                stmt = select(OrganizationMember).where(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.role == "OWNER"
                )
                res = await self._orgs._db.execute(stmt)
                member = res.scalar_one_or_none()
                if member:
                    user = await self._orgs._db.get(User, member.user_id)
                    if user:
                        user.current_organization_id = org_id
                        logger.info(f"[Service] Force user {user.id} context to Org {org_id}")
        if kwargs.get("onboarding_step") is not None:
            org_model.onboarding_step = str(kwargs["onboarding_step"])
            
        await self._orgs._db.flush()
        await self._orgs._db.commit()
        
        logger.success(f"[Service] Org {org_id} saved successfully. Final state in DB model: onboarding_completed={org_model.onboarding_completed}")
        
        from modules.auth.infrastructure.mappers import org_to_entity
        entity = org_to_entity(org_model)
        logger.debug(f"[Service] Returning entity for Org {org_id}: onboarding_completed={entity.onboarding_completed}")
        return entity

    async def remove_member(self, org_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Retire un membre d'une organisation."""
        await self._memberships.delete(org_id, user_id)
        await self._memberships._db.flush()
        return True

    async def update_member_role(self, org_id: uuid.UUID, user_id: uuid.UUID, role: UserRole) -> bool:
        """Change le rôle d'un membre."""
        membership = await self._memberships.update_role(org_id, user_id, role)
        return membership is not None

    async def update_member_permissions(self, org_id: uuid.UUID, user_id: uuid.UUID, permissions: dict) -> bool:
        """Met à jour les permissions granulaires d'un membre."""
        membership = await self._memberships.update_permissions(org_id, user_id, permissions)
        return membership is not None

    async def delete_invitation(self, invitation_id: uuid.UUID) -> bool:
        """Supprime une invitation."""
        return await self._invitations.delete_by_id(invitation_id)
