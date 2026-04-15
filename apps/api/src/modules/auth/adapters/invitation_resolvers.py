"""
Invitation Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import strawberry
from typing import Optional, List
import uuid

from exceptions import UnauthenticatedException
from src.core.graphql.types import InvitationType

@strawberry.type
class InvitationQuery:
    @strawberry.field(name="pendingInvitations")
    async def pending_invitations(self, info) -> List[InvitationType]:
        """Liste les invitations en attente pour l'organisation active."""
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

@strawberry.type
class InvitationMutation:
    @strawberry.mutation
    async def invite_member(self, info, email: str, role: str) -> InvitationType:
        """Invite un nouveau collaborateur."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        from src.modules.auth.infrastructure.models import UserRole
        service = info.context.services.org_service
        invitation = await service.create_invitation(
            email=email,
            organization_id=uuid.UUID(str(info.context.org_id)),
            role=UserRole(role.upper()),
            invited_by_id=uuid.UUID(str(info.context.user_id))
        )
        
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
    async def accept_invitation(self, info, code: str) -> bool:
        """Accepte une invitation."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.org_service
        return await service.accept_invitation(
            code=code,
            user_id=uuid.UUID(str(info.context.user_id))
        )

    @strawberry.mutation
    async def delete_invitation(self, info, invitation_id: strawberry.ID) -> bool:
        """Supprime/Annule une invitation."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.org_service
        return await service.delete_invitation(uuid.UUID(str(invitation_id)))
