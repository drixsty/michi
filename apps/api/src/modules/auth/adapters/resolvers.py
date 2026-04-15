from core.database.models import Organization, User, OrganizationMember
"""
Auth Resolvers — Adapters Layer
Thin resolvers delegating to Application Services.
"""
import strawberry
import uuid

from core.exceptions import UnauthenticatedException, MichiException, ErrorCode
from core.graphql.types import (
    UserType, LoginInput, AuthPayload, RegisterInput, 
    GoogleLoginInput, ChangePasswordInput, UpdateProfileInput
)

@strawberry.type
class AuthQuery:
    @strawberry.field
    async def me(self, info) -> UserType:
        """Récupère l'utilisateur connecté."""
        if not info.context.user_id:
            raise UnauthenticatedException()

        service = info.context.services.auth_service
        user = await service.get_user_by_id(uuid.UUID(str(info.context.user_id)))
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
        
        return AuthPayload(
            token=result.token.value,
            user=UserType.from_db(result.user_model)
        )

    @strawberry.mutation
    async def register(self, info, input: RegisterInput) -> AuthPayload:
        """Inscription manuelle."""
        service = info.context.services.auth_service
        result = await service.register(
            email=input.email,
            password=input.password,
            first_name=input.first_name,
            last_name=input.last_name
        )
        
        return AuthPayload(
            token=result.token.value,
            user=UserType.from_db(result.user_model)
        )

    @strawberry.mutation
    async def google_login(self, info, input: GoogleLoginInput) -> AuthPayload:
        """Authentification via Google (MVP simplified)."""
        # Note: Dans une version réelle, on validerait le token via un provider
        # Ici on simule ou on utilise les infos transmises si sécurisé par ailleurs
        raise MichiException(message="Google Login non implémenté dans l'adaptateur", code=ErrorCode.NOT_FOUND)

    @strawberry.mutation
    async def change_password(self, info, input: ChangePasswordInput) -> bool:
        """Changement de mot de passe."""
        if not info.context.user_id:
            raise UnauthenticatedException()
            
        service = info.context.services.auth_service
        return await service.change_password(
            user_id=uuid.UUID(str(info.context.user_id)),
            current_password=input.current_password,
            new_password=input.new_password
        )

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

        return UserType.from_db(updated_user)
