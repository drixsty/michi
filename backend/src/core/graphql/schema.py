"""
Schema GraphQL Principal
"""
import strawberry
from typing import List, Optional
from loguru import logger
import uuid
import json
from sqlalchemy import select

from .types import (
    UserType, LoginInput, AuthPayload, UpdateProfileInput, 
    ChangePasswordInput, SourceType, InvitationType, 
    OrganizationMemberType, OrganizationType, UpdateOrganizationInput,
    RegisterInput, GoogleLoginInput
)
from src.modules.auth.service import AuthService
from src.modules.auth.invitation_service import InvitationService
from src.modules.shopify.resolvers import ShopifyQuery, ShopifyMutation
from src.modules.forecasting.resolvers import ForecastingQuery, ForecastingMutation
from src.modules.inventory.resolvers import InventoryQuery, InventoryMutation
from src.modules.decisions.resolvers import DecisionQuery, DecisionMutation
from src.modules.billing.resolvers import BillingQuery, BillingMutation
from src.modules.auth.decorators import require_role, require_permission
from src.modules.auth.constants import MichiPermission
from src.core.exceptions import UnauthenticatedException, MichiException, ErrorCode
import requests


@strawberry.type
class Query(ShopifyQuery, ForecastingQuery, InventoryQuery, DecisionQuery, BillingQuery):
    """Queries GraphQL"""

    @strawberry.field
    async def me(self, info) -> UserType:
        """Récupère l'utilisateur avec ses organisations."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        user = await auth_service.get_user_by_id(info.context.user_id)
        if not user:
            raise UnauthenticatedException()

        # Mapping manuel pour éviter le deadlock Pydantic/SQLAlchemy en async
        return UserType(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            current_organization_id=strawberry.ID(str(user.current_organization_id)) if user.current_organization_id else None,
            shop_id=strawberry.ID(str(user.shop_id)) if user.shop_id else None,
            created_at=user.created_at,
            preferences=json.dumps(user.preferences or {}),
            organizations=[
                OrganizationMemberType(
                    organization_id=strawberry.ID(str(m.organization_id)),
                    user_id=strawberry.ID(str(m.user_id)),
                    role=m.role.value if hasattr(m.role, 'value') else str(m.role),
                    permissions=json.dumps(m.permissions or {}),
                    organization=OrganizationType(
                        id=strawberry.ID(str(m.organization.id)),
                        name=m.organization.name,
                        slug=m.organization.slug,
                        plan=m.organization.plan,
                        subscription_status=m.organization.subscription_status,
                        created_at=m.organization.created_at,
                        settings=json.dumps(m.organization.settings or {})
                    )
                ) for m in user.organizations
            ]
        )

    @strawberry.field
    async def sources(self, info) -> List[SourceType]:
        """Retourne les stores de l'organisation active."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
        
        from src.modules.inventory.models import Store
        from sqlalchemy import select
        
        result = await info.context.db.execute(
            select(Store).where(Store.organization_id == uuid.UUID(str(info.context.org_id)))
        )
        stores = result.scalars().all()
        
        return [
            SourceType(
                id=strawberry.ID(str(s.id)),
                name=s.name,
                platform=s.platform.value,
                connected=s.connected,
                last_sync_at=s.last_sync_at,
                health_status=s.health_status,
                organization_id=strawberry.ID(str(s.organization_id))
            ) for s in stores
        ]

    @strawberry.field(name="organizationMembers")
    async def organization_members(self, info) -> Optional[List[OrganizationMemberType]]:
        """Liste les membres de l'organisation active.

        Retourne une liste vide si l'utilisateur n'a pas de contexte d'organisation
        (pas d'org_id dans le JWT) plutôt que de propager une erreur au niveau racine.
        """
        if not info.context.user_id:
            raise UnauthenticatedException()

        # Pas d'org dans le contexte → liste vide (pas d'erreur racine)
        if not info.context.org_id:
            return []

        from src.modules.auth.models import OrganizationMember
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        try:
            result = await info.context.db.execute(
                select(OrganizationMember)
                .where(OrganizationMember.organization_id == uuid.UUID(str(info.context.org_id)))
                .options(selectinload(OrganizationMember.user))
            )
            members = result.scalars().all()

            return [
                OrganizationMemberType(
                    organization_id=strawberry.ID(str(m.organization_id)),
                    user_id=strawberry.ID(str(m.user_id)),
                    role=m.role.value if hasattr(m.role, 'value') else str(m.role),
                    permissions=json.dumps(m.permissions or {}),
                    user=UserType(
                        id=strawberry.ID(str(m.user.id)),
                        email=m.user.email,
                        first_name=m.user.first_name,
                        last_name=m.user.last_name,
                        created_at=m.user.created_at,
                        preferences=json.dumps(m.user.preferences or {}),
                        organizations=[]
                    ) if m.user else None
                ) for m in members
            ]
        except Exception as exc:
            logger.error(f"[organizationMembers] DB error: {exc}")
            return []

    @strawberry.field(name="pendingInvitations")
    async def pending_invitations(self, info) -> Optional[List[InvitationType]]:
        """Liste les invitations en attente pour l'organisation active."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        if not info.context.org_id:
            return []

        service = InvitationService(info.context.db)
        try:
            invitations = await service.get_pending_invitations(uuid.UUID(str(info.context.org_id)))
        except Exception as exc:
            logger.error(f"[pendingInvitations] get_pending_invitations failed: {exc!r}")
            raise

        try:
            return [
                InvitationType(
                    id=strawberry.ID(str(i.id)),
                    email=i.email,
                    organization_id=strawberry.ID(str(i.organization_id)),
                    role=i.role.value if hasattr(i.role, 'value') else str(i.role),
                    status=i.status.value if hasattr(i.status, 'value') else str(i.status),
                    code=i.code,
                    created_at=i.created_at,
                    expires_at=i.expires_at
                ) for i in invitations
            ]
        except Exception as exc:
            logger.error(f"[pendingInvitations] mapping error on {len(invitations)} rows: {exc!r}")
            raise

    @strawberry.field
    async def currentOrganization(self, info) -> Optional[OrganizationType]:
        """Récupère les détails de l'organisation active."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
        
        from src.modules.auth.models import Organization
        from sqlalchemy import select
        
        result = await info.context.db.execute(
            select(Organization).where(Organization.id == uuid.UUID(str(info.context.org_id)))
        )
        org = result.scalar_one_or_none()
        if not org:
            return None
            
        return OrganizationType(
            id=strawberry.ID(str(org.id)),
            name=org.name,
            slug=org.slug,
            plan=org.plan,
            subscription_status=org.subscription_status,
            created_at=org.created_at,
            settings=json.dumps(org.settings or {})
        )


@strawberry.type
class Mutation(ShopifyMutation, ForecastingMutation, InventoryMutation, DecisionMutation, BillingMutation):
    """Mutations GraphQL"""

    @strawberry.mutation
    async def login(self, info, input: LoginInput) -> AuthPayload:
        """Login SaaS avec support multi-org."""
        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        from src.modules.auth.schemas import LoginInput as LoginInputSchema
        
        result = await auth_service.login(LoginInputSchema(email=input.email, password=input.password))

        user = result.user
        return AuthPayload(
            token=result.token,
            user=UserType(
                id=strawberry.ID(str(user.id)),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                current_organization_id=strawberry.ID(str(user.current_organization_id)) if user.current_organization_id else None,
                shop_id=strawberry.ID(str(user.shop_id)) if user.shop_id else None,
                created_at=user.created_at,
                preferences=json.dumps(user.preferences or {}),
                organizations=[
                    OrganizationMemberType(
                        organization_id=strawberry.ID(str(m.organization_id)),
                        user_id=strawberry.ID(str(m.user_id)),
                        role=m.role.value if hasattr(m.role, 'value') else str(m.role),
                        permissions=json.dumps(m.permissions or {}),
                        organization=OrganizationType(
                            id=strawberry.ID(str(m.organization.id)),
                            name=m.organization.name,
                            slug=m.organization.slug,
                            plan=m.organization.plan,
                            subscription_status=m.organization.subscription_status,
                            created_at=m.organization.created_at,
                            settings=json.dumps(m.organization.settings or {})
                        )
                    ) for m in user.organizations
                ]
            )
        )

    @strawberry.mutation
    async def create_organization(self, info, name: str, plan: str = "BASIC") -> AuthPayload:
        """Crée une nouvelle organisation et retourne un nouveau token avec le contexte."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        import uuid
        from src.modules.auth.models import Organization, OrganizationMember, UserRole
        from src.modules.auth.service import AuthService
        from src.modules.auth.schemas import UserSchema
        from src.core.security import create_access_token
        
        # 1. Créer l'organisation
        slug = f"org-{uuid.uuid4().hex[:8]}"
        org = Organization(
            name=name, 
            slug=slug, 
            plan=plan.upper()
        )
        info.context.db.add(org)
        await info.context.db.flush()
        
        # 2. Lier l'utilisateur
        user_id = uuid.UUID(str(info.context.user_id))
        member = OrganizationMember(
            user_id=user_id,
            organization_id=org.id,
            role=UserRole.ADMIN
        )
        info.context.db.add(member)
        
        # 3. Mettre à jour current_org de l'user
        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        user = await auth_service.get_user_by_id(info.context.user_id)
        if user:
            user.current_organization_id = org.id
            
        await info.context.db.flush()
        
        # 4. Sync Stripe (si activé)
        if info.context.billing:
            stripe_id = await info.context.billing.create_customer(
                name=org.name, 
                email=user.email, 
                org_id=str(org.id)
            )
            if stripe_id:
                org.stripe_customer_id = stripe_id
                await info.context.db.flush()
        
        await info.context.db.commit()
        
        # 5. Refresh token with new org context
        token_data = {
            "user_id": str(user.id),
            "org_id": str(org.id),
            "email": user.email
        }
        new_token = create_access_token(token_data)
        
        # Recharger l'user pour avoir les organizations à jour pour le mapping
        user = await auth_service.get_user_by_id(info.context.user_id)
        
        return AuthPayload(
            token=new_token,
            user=UserType(
                id=strawberry.ID(str(user.id)),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                current_organization_id=strawberry.ID(str(user.current_organization_id)),
                created_at=user.created_at,
                preferences=json.dumps(user.preferences or {}),
                organizations=[
                    OrganizationMemberType(
                        organization_id=strawberry.ID(str(m.organization_id)),
                        user_id=strawberry.ID(str(m.user_id)),
                        role=m.role.value if hasattr(m.role, 'value') else str(m.role),
                        permissions=json.dumps(m.permissions or {}),
                        organization=OrganizationType(
                            id=strawberry.ID(str(m.organization.id)),
                            name=m.organization.name,
                            slug=m.organization.slug,
                            plan=m.organization.plan,
                            subscription_status=m.organization.subscription_status,
                            created_at=m.organization.created_at,
                            settings=json.dumps(m.organization.settings or {})
                        )
                    ) for m in user.organizations
                ]
            )
        )

    @strawberry.mutation
    async def switch_organization(self, info, organization_id: strawberry.ID) -> AuthPayload:
        """Bascule vers une autre organisation et rafraîchit le token."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        user = await auth_service.update_user(
            user_id=info.context.user_id,
            current_organization_id=uuid.UUID(str(organization_id))
        )
        
        from src.core.security import create_access_token
        token = create_access_token({
            "user_id": str(user.id),
            "org_id": str(organization_id),
            "email": user.email
        })
        
        from src.modules.auth.schemas import UserSchema
        user_schema = UserSchema.model_validate(user)

        return AuthPayload(
            token=token,
            user=UserType(
                id=strawberry.ID(str(user_schema.id)),
                email=user_schema.email,
                first_name=user_schema.first_name,
                last_name=user_schema.last_name,
                current_organization_id=strawberry.ID(str(user_schema.current_organization_id)) if user_schema.current_organization_id else None,
                shop_id=strawberry.ID(str(user_schema.shop_id)) if user_schema.shop_id else None,
                created_at=user_schema.created_at,
                preferences=json.dumps(user_schema.preferences or {}),
                organizations=[
                    OrganizationMemberType(
                        organization_id=strawberry.ID(str(m.organization_id)),
                        user_id=strawberry.ID(str(m.user_id)),
                        role=m.role.value if hasattr(m.role, 'value') else str(m.role),
                        permissions=json.dumps(m.permissions or {}),
                        organization=OrganizationType(
                            id=strawberry.ID(str(m.organization.id)),
                            name=m.organization.name,
                            slug=m.organization.slug,
                            plan=m.organization.plan,
                            subscription_status=m.organization.subscription_status,
                            created_at=m.organization.created_at,
                            settings=json.dumps(m.organization.settings or {})
                        )
                    ) for m in user_schema.organizations
                ]
            )
        )

    @strawberry.mutation
    async def update_profile(self, info, input: UpdateProfileInput) -> UserType:
        """Maj profil multi-tenant."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        user = await auth_service.get_user_by_id(info.context.user_id)
        if not user:
            raise UnauthenticatedException()
            
        # Clean current preferences (Relocation Sprint 16)
        # On supprime les anciennes clés qui ont été déplacées vers l'organisation
        current_prefs = dict(user.preferences or {})
        current_prefs.pop("currency", None)
        current_prefs.pop("is_mutualized", None)
        
        # New base prefs
        prefs = current_prefs
        if input.email_alerts_enabled is not None: prefs["email_alerts_enabled"] = input.email_alerts_enabled
        if input.min_severity is not None: prefs["min_severity"] = input.min_severity
            
        user = await auth_service.update_user(
            user_id=info.context.user_id,
            email=input.email,
            preferences=prefs
        )

        return UserType(
            id=strawberry.ID(str(user.id)),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            current_organization_id=strawberry.ID(str(user.current_organization_id)) if user.current_organization_id else None,
            shop_id=strawberry.ID(str(user.shop_id)) if user.shop_id else None,
            created_at=user.created_at,
            preferences=json.dumps(user.preferences or {}),
            organizations=[]
        )

    @strawberry.mutation
    async def register(self, info, input: RegisterInput) -> AuthPayload:
        """Inscription manuelle."""
        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        result = await auth_service.register(
            email=input.email,
            password=input.password,
            first_name=input.first_name,
            last_name=input.last_name
        )
        
        user = result.user
        return AuthPayload(
            token=result.token,
            user=UserType(
                id=strawberry.ID(str(user.id)),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                current_organization_id=strawberry.ID(str(user.current_organization_id)),
                created_at=user.created_at,
                preferences=json.dumps(user.preferences or {}),
                organizations=[]
            )
        )

    @strawberry.mutation
    async def googleLogin(self, info, input: GoogleLoginInput) -> AuthPayload:
        """Auth Google avec vérification de token."""
        # Note: Dans un vrai SaaS on utiliserait google-auth-library
        # Ici on simule ou on utilise l'endpoint tokeninfo pour rester léger
        try:
            resp = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={input.id_token}")
            if resp.status_code != 200:
                raise MichiException(message="Token Google invalide", code=ErrorCode.UNAUTHENTICATED)
            
            payload = resp.json()
            google_id = payload["sub"]
            email = payload["email"]
            first_name = payload.get("given_name")
            last_name = payload.get("family_name")
            
            auth_service = AuthService(info.context.db, billing_service=info.context.billing)
            result = await auth_service.login_with_google(
                google_id=google_id,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            
            user = result.user
            return AuthPayload(
                token=result.token,
                user=UserType(
                    id=strawberry.ID(str(user.id)),
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    current_organization_id=strawberry.ID(str(user.current_organization_id)),
                    created_at=user.created_at,
                    preferences=json.dumps(user.preferences or {}),
                    organizations=[]
                )
            )
        except Exception as e:
            logger.error(f"Google login error: {e}")
            raise MichiException(message="Erreur lors de l'authentification Google", code=ErrorCode.UNAUTHENTICATED)

    @strawberry.mutation
    @require_permission(MichiPermission.SETTINGS_EDIT)
    async def updateOrganization(self, info, input: UpdateOrganizationInput) -> OrganizationType:
        """Met à jour les réglages de l'organisation active."""
            
        from src.modules.auth.models import Organization
        from sqlalchemy import select
        
        # 1. Fetch organization
        result = await info.context.db.execute(
            select(Organization).where(Organization.id == uuid.UUID(str(info.context.org_id)))
        )
        org = result.scalar_one_or_none()
        if not org:
            raise MichiException(message="Organisation non trouvée", code=ErrorCode.NOT_FOUND)
            
        # 2. Update fields
        if input.name:
            org.name = input.name
            
        # 3. Update settings (JSONB)
        current_settings = dict(org.settings or {})
        if input.currency is not None:
            current_settings["currency"] = input.currency
        if input.is_mutualized is not None:
            current_settings["is_mutualized"] = input.is_mutualized
            
        org.settings = current_settings
        
        await info.context.db.commit()
        
        return OrganizationType(
            id=strawberry.ID(str(org.id)),
            name=org.name,
            slug=org.slug,
            plan=org.plan,
            subscription_status=org.subscription_status,
            created_at=org.created_at,
            settings=json.dumps(org.settings or {})
        )

    @strawberry.mutation
    async def change_password(self, info, input: ChangePasswordInput) -> bool:
        """Change le mot de passe de l'utilisateur."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        return await auth_service.change_password(
            user_id=info.context.user_id,
            current_password=input.current_password,
            new_password=input.new_password
        )

    @strawberry.mutation(name="toggleSource")
    @require_permission(MichiPermission.STORES_MANAGE)
    async def toggle_source(self, info, platform: str, connected: bool, store_id: Optional[strawberry.ID] = None) -> SourceType:
        """Gère la connexion/déconnexion d'un Store."""
            
        from src.modules.inventory.models import Store, PlatformSource, Product
        from sqlalchemy import select, delete
        
        # 1. Récupérer ou créer le Store
        plat_enum = PlatformSource(platform.upper())
        if store_id:
            result = await info.context.db.execute(select(Store).where(Store.id == uuid.UUID(str(store_id))))
            store = result.scalar_one_or_none()
        else:
            result = await info.context.db.execute(
                select(Store).where(
                    Store.organization_id == uuid.UUID(str(info.context.org_id)),
                    Store.platform == plat_enum
                )
            )
            store = result.scalar_one_or_none()
        
        if not store:
            store = Store(
                organization_id=uuid.UUID(str(info.context.org_id)),
                platform=plat_enum,
                name=platform.capitalize()
            )
            info.context.db.add(store)
        else:
            # Enforce standardized naming even for existing records
            store.name = platform.capitalize()
            
        store.connected = connected
        
        # 2. Logique destructive
        if not connected:
            logger.warning(f"Disconnecting {platform} for org {info.context.org_id}. Deleting associated products.")
            await info.context.db.execute(delete(Product).where(Product.store_id == store.id))
            
        await info.context.db.commit()
        
        return SourceType(
            id=strawberry.ID(str(store.id)),
            name=store.name,
            platform=store.platform.value,
            connected=store.connected,
            last_sync_at=store.last_sync_at,
            health_status=store.health_status,
            organization_id=strawberry.ID(str(store.organization_id))
        )

    @strawberry.mutation(name="inviteMember")
    @require_permission(MichiPermission.MEMBERS_INVITE)
    async def invite_member(self, info, email: str, role: str) -> InvitationType:
        """Invite un nouveau collaborateur par email."""
        if not info.context.user_id or not info.context.org_id:
            raise UnauthenticatedException()
            
        from src.modules.auth.models import UserRole
        
        service = InvitationService(info.context.db)
        invitation = await service.create_invitation(
            email=email,
            organization_id=uuid.UUID(str(info.context.org_id)),
            role=UserRole(role.lower()),
            invited_by_id=uuid.UUID(str(info.context.user_id))
        )
        
        await info.context.db.commit()
        
        return InvitationType(
            id=strawberry.ID(str(invitation.id)),
            email=invitation.email,
            organization_id=strawberry.ID(str(invitation.organization_id)),
            role=invitation.role.value,
            status=invitation.status.value,
            code=invitation.code,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at
        )

    @strawberry.mutation(name="updateMemberPermissions")
    @require_permission(MichiPermission.MEMBERS_EDIT_ROLE)
    async def update_member_permissions(self, info, user_id: strawberry.ID, permissions: str) -> OrganizationMemberType:
        """Met à jour les permissions granulaires d'un membre."""
        if not info.context.org_id:
            raise UnauthenticatedException()
            
        import json
        from src.modules.auth.models import OrganizationMember
        
        db = info.context.db
        org_id = uuid.UUID(str(info.context.org_id))
        target_user_id = uuid.UUID(str(user_id))
        
        # Charger le membre
        result = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == target_user_id
            )
        )
        member = result.scalar_one_or_none()
        
        if not member:
            raise MichiException(message="Membre non trouvé", code=ErrorCode.NOT_FOUND)
            
        # Parser et mettre à jour les permissions
        try:
            perms_dict = json.loads(permissions)
            member.permissions = perms_dict
            await db.commit()
        except Exception as e:
            raise MichiException(message=f"Format JSON invalide : {str(e)}", code=ErrorCode.INVALID_INPUT)
            
        return OrganizationMemberType(
            organization_id=strawberry.ID(str(member.organization_id)),
            user_id=strawberry.ID(str(member.user_id)),
            role=member.role.value,
            permissions=json.dumps(member.permissions)
        )

    @strawberry.mutation(name="acceptInvitation")
    async def accept_invitation(self, info, code: str) -> bool:
        """Accepte une invitation via son code secret."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = InvitationService(info.context.db)
        success = await service.accept_invitation(
            code=code,
            user_id=uuid.UUID(str(info.context.user_id))
        )
        
        await info.context.db.commit()
        return success

    @strawberry.mutation(name="deleteInvitation")
    @require_permission(MichiPermission.MEMBERS_INVITE)
    async def delete_invitation(self, info, invitation_id: strawberry.ID) -> bool:
        """Annule une invitation pendante."""
            
        service = InvitationService(info.context.db)
        success = await service.delete_invitation(uuid.UUID(str(invitation_id)))
        
        await info.context.db.commit()
        return success

    @strawberry.mutation(name="removeMember")
    @require_permission(MichiPermission.MEMBERS_REMOVE)
    async def remove_member(self, info, user_id: strawberry.ID) -> bool:
        """Retire un membre de l'organisation."""
            
        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        success = await auth_service.remove_member(
            organization_id=uuid.UUID(str(info.context.org_id)),
            user_id=uuid.UUID(str(user_id))
        )
        await info.context.db.commit()
        return success

    @strawberry.mutation(name="updateMemberRole")
    @require_permission(MichiPermission.MEMBERS_EDIT_ROLE)
    async def update_member_role(self, info, user_id: strawberry.ID, role: str) -> bool:
        """Met à jour le rôle d'un membre."""
            
        from src.modules.auth.models import UserRole
        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        member = await auth_service.update_member_role(
            organization_id=uuid.UUID(str(info.context.org_id)),
            user_id=uuid.UUID(str(user_id)),
            role=UserRole(role.lower())
        )
        await info.context.db.commit()
        return member is not None

    @strawberry.mutation(name="toggleUserStatus")
    @require_permission(MichiPermission.MEMBERS_REMOVE)
    async def toggle_user_status(self, info, user_id: strawberry.ID, active: bool) -> bool:
        """Active ou désactive un utilisateur (Ban)."""
            
        auth_service = AuthService(info.context.db, billing_service=info.context.billing)
        user = await auth_service.toggle_user_status(
            user_id=uuid.UUID(str(user_id)),
            is_active=active
        )
        await info.context.db.commit()
        return user is not None


from .extensions import MichiExceptionExtension

# Schema final
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        MichiExceptionExtension,
    ],
)
