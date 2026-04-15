from core.database.models import Organization, User, OrganizationMember
"""
InvitationService : Gestion du cycle de vie des invitations collaborateurs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid
import secrets
from loguru import logger

from .models import Invitation, InvitationStatus, OrganizationMember, UserRole, User
from core.exceptions import MichiException, ErrorCode


class InvitationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invitation(
        self,
        email: str,
        organization_id: uuid.UUID,
        role: UserRole,
        invited_by_id: uuid.UUID
    ) -> Invitation:
        """
        Crée une invitation et simule l'envoi d'email.
        Expiration par défaut : 7 jours.

        Raises:
            MichiException(ALREADY_MEMBER): si l'email correspond à un membre actif.
            MichiException(INVITATION_ALREADY_PENDING): si une invitation PENDING existe déjà.
        """
        # Normalisation systématique en minuscules (Sprint 16 Case Sensitivity Fix)
        email = email.strip().lower()

        # 1. Vérifier si l'utilisateur est déjà membre de l'organisation
        from sqlalchemy import func
        existing_user_result = await self.db.execute(
            select(User).where(func.lower(User.email) == email)
            .options(selectinload(User.organizations))
        )
        existing_user = existing_user_result.scalar_one_or_none()
        if existing_user:
            is_member = any(
                str(m.organization_id) == str(organization_id)
                for m in existing_user.organizations
            )
            if is_member:
                raise MichiException(
                    message=f"L'utilisateur {email} est déjà membre de cette organisation.",
                    code=ErrorCode.ALREADY_MEMBER
                )

        # 2. Vérifier si une invitation PENDING existe déjà — bloquer le doublon
        result = await self.db.execute(
            select(Invitation).where(
                func.lower(Invitation.email) == email,
                Invitation.organization_id == organization_id,
                Invitation.status == InvitationStatus.PENDING
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Si l'invitation existante est expirée, on la supprime pour permettre la nouvelle
            if existing.expires_at < datetime.utcnow():
                logger.info(f"🗑️ Deleting expired invitation for {email}")
                await self.db.delete(existing)
                await self.db.flush()
            else:
                raise MichiException(
                    message=f"Une invitation est déjà en attente pour {email}. Annulez-la d'abord si vous souhaitez la renouveler.",
                    code=ErrorCode.INVITATION_ALREADY_PENDING
                )

        # 3. Générer code unique (US 16.5)
        code = secrets.token_urlsafe(16)

        # 4. Créer record
        invitation = Invitation(
            email=email,
            organization_id=organization_id,
            role=role,
            code=code,
            invited_by_id=invited_by_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        self.db.add(invitation)
        await self.db.flush()

        # 5. Simulation envoi email
        logger.info(f"📧 [INVITATION SIMULÉE] Email: {email} | Code: {code} | Org: {organization_id}")

        return invitation

    async def accept_invitation(self, code: str, user_id: uuid.UUID) -> bool:
        """
        Valide un code d'invitation et ajoute l'utilisateur à l'organisation.
        """
        result = await self.db.execute(
            select(Invitation).where(Invitation.code == code, Invitation.status == InvitationStatus.PENDING)
        )
        invitation = result.scalar_one_or_none()
        
        if not invitation:
            return False
            
        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED
            await self.db.flush()
            return False
            
        # Créer le lien de membre
        member = OrganizationMember(
            user_id=user_id,
            organization_id=invitation.organization_id,
            role=invitation.role
        )
        self.db.add(member)
        
        # Marquer l'invitation comme acceptée
        invitation.status = InvitationStatus.ACCEPTED
        
        # Mettre à jour l'organisation active de l'utilisateur
        result_user = await self.db.execute(select(User).where(User.id == user_id))
        user = result_user.scalar_one_or_none()
        if user:
            user.current_organization_id = invitation.organization_id
            
        await self.db.flush()
        return True

    async def get_pending_invitations(self, organization_id: uuid.UUID) -> list[Invitation]:
        """Liste les invitations ACTIVES (non expirées) pour une org."""
        now = datetime.utcnow()
        result = await self.db.execute(
            select(Invitation).where(
                Invitation.organization_id == organization_id,
                Invitation.status == InvitationStatus.PENDING,
                Invitation.expires_at > now
            )
        )
        return list(result.scalars().all())

    async def delete_invitation(self, invitation_id: uuid.UUID) -> bool:
        """Supprime/Annule une invitation."""
        result = await self.db.execute(select(Invitation).where(Invitation.id == invitation_id))
        inv = result.scalar_one_or_none()
        if inv:
            await self.db.delete(inv)
            await self.db.flush()
            return True
        return False
