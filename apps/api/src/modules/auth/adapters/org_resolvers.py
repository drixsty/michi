"""
Organization Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import strawberry
from typing import Optional, List
import uuid

from core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from core.graphql.types import (
    OrganizationType, OrganizationMemberType, UpdateOrganizationInput,
    AuthPayload, UserType
)

from modules.auth.adapters.decorators import require_permission, rate_limit
from modules.auth.domain.permissions import PermissionCode

@strawberry.type
class OrgQuery:
    @strawberry.field
    async def current_organization(self, info: strawberry.types.Info) -> Optional[OrganizationType]:
        """Récupère les détails de l'organisation active."""
        if not info.context.user_id:
            return None
        
        if not info.context.org_id:
            return None
        
        service = info.context.services.org_service
        org = await service.get_current_org(uuid.UUID(str(info.context.org_id)))
        return OrganizationType.from_db(org) if org else None

    @strawberry.field(name="organizationMembers")
    @require_permission(PermissionCode.SETTINGS_VIEW)
    async def organization_members(self, info: strawberry.types.Info) -> List[OrganizationMemberType]:
        """Liste les membres de l'organisation (MANAGER et au-dessus)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
        
        if not info.context.org_id:
            return []

        service = info.context.services.org_service
        members = await service.get_members_with_users(uuid.UUID(str(info.context.org_id)))
        return [OrganizationMemberType.from_db(m, include_user=True) for m in members]

@strawberry.type
class OrgMutation:
    @strawberry.mutation
    async def create_organization(self, info: strawberry.types.Info, name: str, plan: str = "BASIC") -> AuthPayload:
        """Crée une nouvelle organisation."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.org_service
        result = await service.create_organization(
            user_id=uuid.UUID(str(info.context.user_id)),
            name=name,
            plan=plan,
            email=info.context.email
        )
        
        # On attend commit() si nécessaire, mais le service doit gérer le flush.
        # En Strawberry/FastAPI, le middleware gère le commit en fin de requête.
        
        await info.context.db.commit()
        
        return AuthPayload(
            token=result.token.value,
            user=UserType.from_db(result.user_model)
        )

    @strawberry.mutation
    async def switch_organization(self, info: strawberry.types.Info, organization_id: strawberry.ID) -> AuthPayload:
        """Bascule de contexte d'organisation."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.org_service
        token, user_model = await service.switch_organization(
            user_id=uuid.UUID(str(info.context.user_id)),
            organization_id=uuid.UUID(str(organization_id))
        )
        
        await info.context.db.commit()
        
        return AuthPayload(
            token=token.value,
            user=UserType.from_db(user_model)
        )

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_EDIT)
    async def update_organization(self, info: strawberry.types.Info, input: UpdateOrganizationInput) -> Optional[OrganizationType]:
        """Met à jour les informations de l'organisation (Nom, Devise, Mutualisation)."""
        user_id = info.context.user_id
        if not user_id:
            raise UnauthenticatedException("Utilisateur non authentifié")
            
        org_id = info.context.org_id
        if not org_id:
            # Fallback pour l'onboarding: si pas d'org dans le token, on prend la seule org de l'utilisateur
            from modules.auth.infrastructure.models import OrganizationMember
            from sqlalchemy import select
            stmt = select(OrganizationMember).where(OrganizationMember.user_id == user_id)
            res = await info.context.db.execute(stmt)
            memberships = res.scalars().all()
            if len(memberships) == 1:
                org_id = memberships[0].organization_id
            else:
                raise UnauthenticatedException("Contexte organisationnel introuvable. Veuillez vous reconnecter.")
            
        settings_dict = {}
        if input.currency is not None:
            settings_dict["currency"] = input.currency
        if input.is_mutualized is not None:
            settings_dict["is_mutualized"] = input.is_mutualized
        if input.report_enabled is not None:
            settings_dict["report_enabled"] = input.report_enabled
        if input.report_frequency is not None:
            settings_dict["report_frequency"] = input.report_frequency
        if input.report_recipients is not None:
            settings_dict["report_recipients"] = input.report_recipients

        # Extraction robuste (supporte snake_case et camelCase sur l'objet Python)
        onboarding_completed = getattr(input, "onboarding_completed", getattr(input, "onboardingCompleted", None))
        onboarding_step = getattr(input, "onboarding_step", getattr(input, "onboardingStep", None))

        from loguru import logger
        logger.info(f"[Resolver] Update Org Input: name={input.name}, completed={onboarding_completed}, step={onboarding_step}")

        service = info.context.services.org_service
        updated_org = await service.update_organization(
            org_id=uuid.UUID(str(org_id)),
            name=input.name,
            settings=settings_dict if settings_dict else None,
            onboarding_completed=onboarding_completed,
            onboarding_step=onboarding_step
        )
        
        try:
            await info.context.db.commit()
            logger.success(f"[Resolver] Commit Success for Org {info.context.org_id}")
        except Exception as e:
            logger.error(f"[Resolver] Commit Failed: {str(e)}")
            await info.context.db.rollback()
            raise MichiException("Database commit failed", ErrorCode.INTERNAL_ERROR)

        return OrganizationType.from_db(updated_org) if updated_org else None

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_MANAGE_MEMBERS)
    async def remove_member(self, info: strawberry.types.Info, user_id: strawberry.ID) -> bool:
        """Retire un membre de l'organisation."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        service = info.context.services.org_service
        res = await service.remove_member(
            org_id=uuid.UUID(str(info.context.org_id)),
            user_id=uuid.UUID(str(user_id))
        )
        await info.context.db.commit()
        return res

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_MANAGE_MEMBERS)
    async def update_member_role(self, info: strawberry.types.Info, user_id: strawberry.ID, role: str) -> bool:
        """Change le rôle d'un collaborateur."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        from core.database.models import UserRole
        service = info.context.services.org_service
        res = await service.update_member_role(
            org_id=uuid.UUID(str(info.context.org_id)),
            user_id=uuid.UUID(str(user_id)),
            role=UserRole(role.upper())
        )
        await info.context.db.commit()
        return res

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_MANAGE_MEMBERS)
    async def update_member_permissions(self, info: strawberry.types.Info, user_id: strawberry.ID, permissions: str) -> Optional[OrganizationMemberType]:
        """Met à jour les permissions granulaires d'un membre (permissions passées en string JSON)."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        import json
        try:
            perms_dict = json.loads(permissions)
        except json.JSONDecodeError:
            raise MichiException(message="Format JSON invalide pour les permissions", code=ErrorCode.BAD_REQUEST)

        service = info.context.services.org_service
        org_id = uuid.UUID(str(info.context.org_id))
        target_user_id = uuid.UUID(str(user_id))
        
        success = await service.update_member_permissions(
            org_id=org_id,
            user_id=target_user_id,
            permissions=perms_dict
        )
        
        await info.context.db.commit()
        
        if not success:
            return None
            
        # Récupération du membre mis à jour pour le cache Apollo
        members = await service.get_members_with_users(org_id)
        member = next((m for m in members if m.user_id == target_user_id), None)
        
        return OrganizationMemberType.from_db(member, include_user=True) if member else None
