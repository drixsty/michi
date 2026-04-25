from core.database.models import Organization, User, OrganizationMember
"""
Auth Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import strawberry
import uuid
import json

import httpx
from core.config import settings
from core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from core.graphql.types import (
    UserType, LoginInput, AuthPayload, RegisterInput, 
    GoogleLoginInput, ChangePasswordInput, UpdateProfileInput,
    RequestPasswordResetInput, ResetPasswordInput, TwoFactorSetupType,
    UserDataExportType, TwoFactorConfirmResult
)
from modules.auth.adapters.decorators import require_permission, rate_limit
from modules.auth.domain.permissions import PermissionCode

@strawberry.type
class AuthQuery:
    @strawberry.field
    async def me(self, info) -> UserType:
        """Récupère l'utilisateur connecté."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = info.context.services.auth_service
        # Force eager load of organizations and their nested organization models
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from core.database.models import User, OrganizationMember, Organization
        
        stmt = (
            select(User)
            .where(User.id == uuid.UUID(str(info.context.user_id)))
            .options(
                selectinload(User.organizations).selectinload(OrganizationMember.organization)
            )
        )
        res = await info.context.db.execute(stmt)
        user = res.scalars().first()
        
        if not user:
            raise UnauthenticatedException()
            
        return UserType.from_db(user)

@strawberry.type
class AuthMutation:
    @strawberry.mutation
    async def login(self, info, input: LoginInput) -> AuthPayload:
        """Authentification par email/password."""
        service = info.context.services.auth_service
        result = await service.login(email=input.email, password=input.password)
        await info.context.db.commit()
        
        return AuthPayload(
            token=result.token.value if result.token and result.token.value else None,
            user=UserType.from_db(result.user_model) if result.user_model else None,
            mfa_required=result.mfa_required,
            mfa_token=result.mfa_token
        )

    @strawberry.mutation
    async def register(self, info, input: RegisterInput) -> AuthPayload:
        """Inscription manuelle. Gère le cas invitation si invitation_code fourni."""
        service = info.context.services.auth_service
        result = await service.register(
            email=input.email,
            password=input.password,
            first_name=input.first_name,
            last_name=input.last_name,
            create_default_org=not bool(input.invitation_code)
        )
        await info.context.db.commit()

        # Si un code d'invitation est fourni, l'accepter immédiatement
        if input.invitation_code:
            try:
                org_service = info.context.services.org_service
                await org_service.accept_invitation(
                    code=input.invitation_code,
                    user_id=result.user_model.id
                )
                await info.context.db.commit()
                # Recharger l'utilisateur pour avoir les orgs à jour
                result.user_model = await service.get_user_model_by_id(result.user_model.id)
            except Exception as e:
                from loguru import logger
                logger.warning(f"[Register] Invitation acceptance failed for code={input.invitation_code}: {e}")

        return AuthPayload(
            token=result.token.value,
            user=UserType.from_db(result.user_model)
        )

    @strawberry.mutation
    async def google_login(self, info, input: GoogleLoginInput) -> AuthPayload:
        """Authentification via Google (SaaS)."""
        # 1. Vérification du jeton ID Google auprès de Google
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={input.id_token}",
                    timeout=5.0
                )
                if response.status_code != 200:
                    raise MichiException(message="Jeton Google invalide ou expiré", code=ErrorCode.UNAUTHENTICATED)
                
                payload = response.json()
            except MichiException:
                raise
            except Exception as e:
                from loguru import logger
                logger.error(f"Google Token Verification Error: {str(e)}")
                raise MichiException(message="Erreur de vérification Google", code=ErrorCode.INTERNAL_ERROR)

        # 2. Validation de l'audience (client_id)
        if payload.get("aud") != settings.GOOGLE_CLIENT_ID:
            from loguru import logger
            logger.warning(f"Google Login Audience mismatch: {payload.get('aud')} vs {settings.GOOGLE_CLIENT_ID}")
            raise MichiException(message="Audience Google invalide", code=ErrorCode.UNAUTHENTICATED)

        # 3. Extraction des infos
        email = payload.get("email")
        google_id = payload.get("sub")
        first_name = payload.get("given_name", "")
        last_name = payload.get("family_name", "")

        # 4. Appel au service applicatif
        service = info.context.services.auth_service
        result = await service.login_with_google(
            google_id=google_id,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        await info.context.db.commit()

        # 5. Gestion du code d'invitation (si présent)
        if input.invitation_code and result.user_model:
            try:
                org_service = info.context.services.org_service
                await org_service.accept_invitation(
                    code=input.invitation_code,
                    user_id=result.user_model.id
                )
                await info.context.db.commit()
                result.user_model = await service.get_user_model_by_id(result.user_model.id)
            except Exception as e:
                from loguru import logger
                logger.warning(f"[GoogleLogin] Invitation acceptance failed: {e}")

        return AuthPayload(
            token=result.token.value,
            user=UserType.from_db(result.user_model)
        )

    @strawberry.mutation
    async def verify_email(self, info, token: str) -> bool:
        """Valide le jeton de vérification de l'e-mail."""
        service = info.context.services.auth_service
        
        # Si l'utilisateur est déjà connecté et déjà vérifié, on renvoie True (Idempotence)
        if info.context.user_id:
            user_model = await service.get_user_model_by_id(info.context.user_id)
            if user_model and user_model.email_verified_at:
                return True

        success = await service.verify_email(token)
        if success:
            await info.context.db.commit()
        return success

    @strawberry.mutation
    @rate_limit(max_calls=3, window_seconds=600)  # 3 renvois max / 10 min
    async def resend_verification_email(self, info, email: str) -> bool:
        """Rénvoie l'e-mail de vérification."""
        service = info.context.services.auth_service
        success = await service.resend_verification_email(email)
        if success:
            await info.context.db.commit()
        return success

    @strawberry.mutation
    @rate_limit(max_calls=10, window_seconds=900)  # 10 tentatives / 15 min
    async def change_password(self, info, input: ChangePasswordInput) -> bool:
        """Changement de mot de passe."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.auth_service
        res = await service.change_password(
            user_id=uuid.UUID(str(info.context.user_id)),
            current_password=input.current_password,
            new_password=input.new_password
        )
        await info.context.db.commit()
        return res

    @strawberry.mutation
    async def update_profile(self, info, input: UpdateProfileInput) -> UserType:
        """Mise à jour du profil utilisateur."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = info.context.services.auth_service
        
        # Logique de nettoyage des préférences (Relocation Sprint 16)
        user_entity = await service.get_user_by_id(uuid.UUID(str(info.context.user_id)))
        if not user_entity:
            raise UnauthenticatedException()
            
        prefs = dict(user_entity.preferences or {})
        if input.email_alerts_enabled is not None: prefs["email_alerts_enabled"] = input.email_alerts_enabled
        if input.min_severity is not None: prefs["min_severity"] = input.min_severity
            
        updated_user = await service.update_user(
            user_id=uuid.UUID(str(info.context.user_id)),
            email=input.email,
            first_name=input.first_name,
            last_name=input.last_name,
            preferences=prefs
        )
        await info.context.db.commit()
        return UserType.from_db(updated_user)

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_MANAGE_MEMBERS)
    async def toggle_user_status(self, info, user_id: strawberry.ID, active: bool) -> bool:
        """Active ou désactive un compte utilisateur."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.auth_service
        result = await service.toggle_user_status(
            user_id=uuid.UUID(str(user_id)),
            is_active=active
        )
        await info.context.db.commit()
        return result is not None

    @strawberry.mutation
    @rate_limit(max_calls=3, window_seconds=3600)  # 3 demandes / heure (anti-spam)
    async def forgot_password(self, info, input: RequestPasswordResetInput) -> bool:
        """Demande de réinitialisation de mot de passe."""
        service = info.context.services.auth_service
        return await service.request_password_reset(input.email)

    @strawberry.mutation
    async def reset_password(self, info, input: ResetPasswordInput) -> bool:
        """Réinitialisation effective du mot de passe via token."""
        service = info.context.services.auth_service
        return await service.reset_password(input.token, input.new_password)

    # --- 2FA Mutations ---

    @strawberry.mutation
    async def setup_2fa(self, info) -> TwoFactorSetupType:
        """Initialise la configuration du 2FA."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        from modules.auth.application.two_factor_service import TwoFactorService
        service = TwoFactorService()
        result = await service.setup_2fa(str(info.context.user_id))
        return TwoFactorSetupType(
            secret=result["secret"],
            provisioning_uri=result["provisioning_uri"]
        )

    @strawberry.mutation
    async def confirm_2fa(self, info, secret: str, code: str) -> TwoFactorConfirmResult:
        """Valide et active le 2FA."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        from modules.auth.application.two_factor_service import TwoFactorService
        service = TwoFactorService()
        recovery_codes = await service.confirm_2fa(str(info.context.user_id), secret, code)
        
        return TwoFactorConfirmResult(
            success=recovery_codes is not None,
            recovery_codes=recovery_codes
        )

    @strawberry.mutation
    async def disable_2fa(self, info) -> bool:
        """Désactive le 2FA."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        from modules.auth.application.two_factor_service import TwoFactorService
        service = TwoFactorService()
        return await service.disable_2fa(str(info.context.user_id))

    @strawberry.mutation
    async def verify_2fa(self, info, mfa_token: str, code: str) -> AuthPayload:
        """Valide le code 2FA (TOTP ou Recovery Code) pour finaliser le login."""
        service = info.context.services.auth_service
        
        # 1. Décoder le mfa_token pour récupérer le user_id
        payload = service._tokens.decode_token(mfa_token)
        user_id = uuid.UUID(payload["sub"])
        
        # 2. Récupérer le modèle de l'utilisateur
        user_model = await service.get_user_model_by_id(user_id)
        if not user_model or not user_model.two_factor_enabled:
            raise UnauthenticatedException("2FA non activé")
            
        from modules.auth.application.two_factor_service import TwoFactorService
        tf_service = TwoFactorService()
        
        # 3. Vérifier le code (TOTP ou Recovery)
        clean_code = code.strip().upper()
        
        if len(clean_code) == 8:
            # Tentative avec un code de secours
            new_recovery_codes = tf_service.verify_recovery_code(user_model.recovery_codes, clean_code)
            if new_recovery_codes is None:
                raise MichiException(message="Code de secours invalide ou déjà utilisé", code=ErrorCode.UNAUTHENTICATED)
            
            # Code valide ! On met à jour la liste des codes restants
            user_model.recovery_codes = new_recovery_codes
            # Note: SQLAlchemy marquera le champ JSON comme modifié automatiquement
        else:
            # Tentative TOTP standard
            if not tf_service.verify_code(user_model.two_factor_secret, clean_code):
                raise MichiException(message="Code d'authentification invalide", code=ErrorCode.UNAUTHENTICATED)
            
        # 4. Générer le token final
        token = service._tokens.create_access_token(
            user_id=user_model.id,
            org_id=user_model.current_organization_id,
            email=user_model.email,
        )
        
        # Sauvegarder les changements (pour les recovery codes consommés)
        await info.context.db.commit()
        
        return AuthPayload(
            token=token.value,
            user=UserType.from_db(user_model)
        )

    # --- GDPR Mutations ---

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_EXPORT)
    async def export_user_data(self, info) -> UserDataExportType:
        """Exporte l'intégralité des données utilisateur (RGPD)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        from modules.auth.application.gdpr_service import GdprService
        service = GdprService()
        data_json = await service.export_all_user_data(uuid.UUID(str(info.context.user_id)))
        return UserDataExportType(data_json=data_json)

    @strawberry.mutation
    @require_permission(PermissionCode.ORG_DELETE)
    async def delete_account(self, info) -> bool:
        """Supprime définitivement le compte et les données (RGPD - Réservé aux Admins pour sécurité)."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        from modules.auth.application.gdpr_service import GdprService
        service = GdprService()
        return await service.delete_user_account(uuid.UUID(str(info.context.user_id)))
