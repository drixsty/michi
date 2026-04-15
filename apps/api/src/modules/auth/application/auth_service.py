from core.database.models import Organization, User, OrganizationMember
"""
Application AuthService (DDD) — Sprint 21.

Service applicatif d'authentification. Reçoit des ports (interfaces) par injection.
Aucune dépendance SQLAlchemy directe — pur Python.

Remplace progressivement auth/service.py (backward compat conservée le temps
que les resolvers migrent via US 21.9).
"""

import uuid
from dataclasses import dataclass
from typing import Optional

from modules.auth.domain.entities import UserEntity
from modules.auth.domain.ports import (
    IOrganizationRepository,
    IPasswordHasher,
    ITokenService,
    IUserRepository,
)
from modules.auth.domain.value_objects import Email, JwtToken
from modules.auth.infrastructure.repositories import (
    SQLAlchemyMembershipRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyUserRepository,
)
from modules.auth.infrastructure.persistence.models import (
    Organization,
    OrganizationMember,
    User,
    UserRole,
)
from core.exceptions import ErrorCode, MichiException, UnauthenticatedException


@dataclass
class AuthResult:
    """Résultat d'une opération d'authentification."""
    token: JwtToken
    user_model: User  # conservé pour compatibilité avec les schemas Pydantic existants


class ApplicationAuthService:
    """
    Service d'authentification — couche Application (DDD hexagonal).

    Reçoit tous ses ports par injection (constructeur).
    Ne connaît ni SQLAlchemy ni FastAPI.
    """

    def __init__(
        self,
        user_repo: SQLAlchemyUserRepository,
        org_repo: SQLAlchemyOrganizationRepository,
        membership_repo: SQLAlchemyMembershipRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        billing_service=None,
    ) -> None:
        self._users = user_repo
        self._orgs = org_repo
        self._memberships = membership_repo
        self._hasher = password_hasher
        self._tokens = token_service
        self._billing = billing_service

    async def login(self, email: str, password: str) -> AuthResult:
        """
        Authentifie par email + password.

        Raises:
            UnauthenticatedException: si email inconnu ou password incorrect.
        """
        user_model = await self._users.get_model_by_email(email)
        if not user_model:
            raise UnauthenticatedException("Invalid email or password")

        if not user_model.hashed_password:
            raise UnauthenticatedException("Compte Google-only — utilisez Google Login")

        from modules.auth.domain.value_objects import HashedPassword
        hashed = HashedPassword(user_model.hashed_password)
        if not self._hasher.verify(password, hashed):
            raise UnauthenticatedException("Invalid email or password")

        # Org active : utiliser current ou première membership
        active_org_id = user_model.current_organization_id
        if not active_org_id and user_model.organizations:
            active_org_id = user_model.organizations[0].organization_id
            user_model.current_organization_id = active_org_id
            await self._users._db.flush()

        token = self._tokens.create_access_token(
            user_id=user_model.id,
            org_id=active_org_id,
            email=user_model.email,
        )
        return AuthResult(token=token, user_model=user_model)

    async def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> AuthResult:
        """
        Crée un compte utilisateur sans organisation.
        L'onboarding (création d'org) est géré séparément.

        Raises:
            MichiException(ALREADY_MEMBER): si email déjà utilisé.
        """
        email = email.strip().lower()
        existing = await self._users.get_model_by_email(email)
        if existing:
            raise MichiException(
                message="Cet email est déjà utilisé", code=ErrorCode.ALREADY_MEMBER
            )

        from modules.auth.domain.value_objects import HashedPassword
        hashed = self._hasher.hash(password)
        user_model = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed.value,
            organizations=[],
        )
        await self._users.save(user_model)
        
        # Explicit commit to ensure user is visible to immediate subsequent requests (e.g., onboarding)
        await self._users._db.commit()
        print(f">>> [DEBUG] REGISTERED USER ID: {user_model.id} (EMAIL: {user_model.email}) <<<")

        token = self._tokens.create_access_token(
            user_id=user_model.id,
            org_id=None,
            email=user_model.email,
        )
        return AuthResult(token=token, user_model=user_model)

    async def login_with_google(
        self,
        google_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
    ) -> AuthResult:
        """
        Authentification Google OAuth2.
        Crée un compte + organisation par défaut si l'utilisateur n'existe pas encore.
        """
        email = email.strip().lower()

        # Recherche par google_id ou email
        user_model = await self._users.get_model_by_email(email)
        if not user_model:
            google_model = await self._users.get_by_google_id(google_id)
            if google_model:
                user_model = await self._users.get_model_by_id(google_model.id)

        if not user_model:
            # Création auto compte + org
            user_model = User(
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                hashed_password=None,
            )
            await self._users.save(user_model)

            org_name = f"Michi de {first_name or email.split('@')[0]}"
            org_model = Organization(
                name=org_name,
                slug=f"org-{uuid.uuid4().hex[:8]}",
            )
            await self._orgs.save(org_model)

            member = OrganizationMember(
                user_id=user_model.id,
                organization_id=org_model.id,
                role=UserRole.ADMIN,
            )
            await self._memberships.save(member)
            user_model.current_organization_id = org_model.id
            await self._users._db.flush()

            if self._billing:
                stripe_id = await self._billing.create_customer(
                    name=org_model.name,
                    email=user_model.email,
                    org_id=str(org_model.id),
                )
                if stripe_id:
                    org_model.stripe_customer_id = stripe_id
                    await self._users._db.flush()

        token = self._tokens.create_access_token(
            user_id=user_model.id,
            org_id=user_model.current_organization_id,
            email=user_model.email,
        )
        return AuthResult(token=token, user_model=user_model)

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserEntity]:
        """Récupère un utilisateur par son ID."""
        return await self._users.get_by_id(user_id)

    async def get_user_model_by_id(self, user_id: uuid.UUID):
        """Retourne le modèle SQLAlchemy avec relations (organisations) chargées — pour les resolvers GraphQL."""
        return await self._users.get_model_by_id(user_id)

    async def update_user(self, user_id: uuid.UUID, **kwargs) -> Optional[UserEntity]:
        """
        Met à jour un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur.
            **kwargs: Champs à mettre à jour (email, first_name, last_name, preferences, is_active, current_organization_id).
        """
        user_entity = await self._users.get_by_id(user_id)
        if not user_entity:
            return None
        
        # Mise à jour des champs autorisés
        if "email" in kwargs and kwargs["email"]:
            user_entity.email = Email(kwargs["email"])
        if "first_name" in kwargs:
            user_entity.first_name = kwargs["first_name"]
        if "last_name" in kwargs:
            user_entity.last_name = kwargs["last_name"]
        if "preferences" in kwargs:
            user_entity.preferences = kwargs["preferences"]
        if "is_active" in kwargs:
            user_entity.is_active = kwargs["is_active"]
        if "current_organization_id" in kwargs:
            user_entity.current_organization_id = kwargs["current_organization_id"]
            
        return await self._users.update(user_entity)

    async def change_password(
        self, 
        user_id: uuid.UUID, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change le mot de passe d'un utilisateur.
        """
        user_model = await self._users.get_model_by_id(user_id)
        if not user_model or not user_model.hashed_password:
            return False
            
        from modules.auth.domain.value_objects import HashedPassword
        if not self._hasher.verify(current_password, HashedPassword(user_model.hashed_password)):
            raise MichiException(message="Mot de passe actuel incorrect", code=ErrorCode.UNAUTHENTICATED)
            
        new_hashed = self._hasher.hash(new_password)
        user_model.hashed_password = new_hashed.value
        await self._users._db.flush()
        return True

    async def toggle_user_status(self, user_id: uuid.UUID, is_active: bool) -> Optional[UserEntity]:
        """Active ou désactive un utilisateur."""
        user_entity = await self._users.get_by_id(user_id)
        if not user_entity:
            return None
            
        user_entity.is_active = is_active
        return await self._users.update(user_entity)
