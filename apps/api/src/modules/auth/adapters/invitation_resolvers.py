"""
Invitation Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import strawberry
from typing import Optional, List
import uuid

from core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from core.graphql.types import InvitationType, InvitationPreviewType
from modules.auth.adapters.decorators import require_permission, rate_limit
from modules.auth.domain.permissions import PermissionCode

@strawberry.type
class InvitationQuery:
    @strawberry.field(name="pendingInvitations")
    @require_permission(PermissionCode.ORG_MANAGE_MEMBERS)
    async def pending_invitations(self, info: strawberry.types.Info) -> List[InvitationType]:
        """Liste les invitations en attente (ADMIN/OWNER uniquement — évite la fuite d'emails)."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        if not info.context.org_id:
            return []

        service = info.context.services.org_service
        invitations = await service.get_pending_invitations(uuid.UUID(str(info.context.org_id)))
        
        return [
            InvitationType(
                id=strawberry.ID(str(i.id)),
                email=i.email.value if hasattr(i.email, 'value') else str(i.email),
                organization_id=strawberry.ID(str(i.organization_id)),
                role=i.role.name if hasattr(i.role, 'name') else str(i.role),
                status=i.status.name if hasattr(i.status, 'name') else str(i.status),
                code=i.code,
                created_at=i.created_at,
                expires_at=i.expires_at
            ) for i in invitations
        ]

    @strawberry.field(name="invitationPreview")
    async def invitation_preview(self, info: strawberry.types.Info, code: str) -> InvitationPreviewType:
        """Récupère les détails publics d'une invitation via son code (Pas d'authentification requise)."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from modules.auth.infrastructure.persistence.models import Invitation
        from core.database.models import User

        stmt = (
            select(Invitation)
            .options(selectinload(Invitation.organization))
            .where(Invitation.code == code)
        )
        res = await info.context.db.execute(stmt)
        invitation = res.scalars().first()

        if not invitation:
            raise MichiException(message="Invitation introuvable ou invalide", code=ErrorCode.NOT_FOUND)

        if str(invitation.status).split(".")[-1] != "PENDING":
             raise MichiException(message="Cette invitation n'est plus valide", code=ErrorCode.BAD_REQUEST)

        invited_by_name = "Utilisateur inconnu"
        invited_by_email = ""
        
        if invitation.invited_by_id:
             user_res = await info.context.db.execute(select(User).where(User.id == invitation.invited_by_id))
             inviting_user = user_res.scalars().first()
             if inviting_user:
                 invited_by_name = f"{inviting_user.first_name} {inviting_user.last_name}".strip()
                 invited_by_email = inviting_user.email

        return InvitationPreviewType(
            organization_name=invitation.organization.name if invitation.organization else "Organisation Inconnue",
            role=str(invitation.role).split(".")[-1],
            invited_by_name=invited_by_name,
            invited_by_email=invited_by_email,
            expires_at=invitation.expires_at
        )

from modules.auth.adapters.decorators import require_permission, rate_limit
from modules.auth.domain.permissions import PermissionCode

@strawberry.type
class InvitationMutation:
    @strawberry.mutation
    @require_permission(PermissionCode.ORG_MANAGE_MEMBERS)
    @rate_limit(max_calls=5, window_seconds=3600)  # Max 5 invitations/heure/user
    async def invite_member(self, info: strawberry.types.Info, email: str, role: str) -> InvitationType:
        """Invite un nouveau collaborateur (Réservé aux Admins)."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        from core.database.models import UserRole
        service = info.context.services.org_service
        invitation = await service.create_invitation(
            email=email,
            organization_id=uuid.UUID(str(info.context.org_id)),
            role=UserRole(role.upper()),
            invited_by_id=uuid.UUID(str(info.context.user_id))
        )
        
        await info.context.db.commit()
        
        return InvitationType(
            id=strawberry.ID(str(invitation.id)),
            email=invitation.email,
            organization_id=strawberry.ID(str(invitation.organization_id)),
            role=str(invitation.role),
            status=str(invitation.status),
            code=invitation.code,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at
        )

    @strawberry.mutation
    async def accept_invitation(self, info: strawberry.types.Info, code: str) -> bool:
        """Accepte une invitation (Ouvert à l'invité)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.org_service
        res = await service.accept_invitation(
            code=code,
            user_id=uuid.UUID(str(info.context.user_id))
        )
        await info.context.db.commit()
        return res

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_MANAGE_MEMBERS)
    async def delete_invitation(self, info: strawberry.types.Info, invitation_id: strawberry.ID) -> bool:
        """Supprime/Annule une invitation (Réservé aux Admins)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.org_service
        res = await service.delete_invitation(uuid.UUID(str(invitation_id)))
        await info.context.db.commit()
        return res
