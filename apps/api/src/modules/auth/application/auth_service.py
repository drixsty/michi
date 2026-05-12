from core.database.models import Organization, User, OrganizationMember
"""
Application AuthService (DDD) — Sprint 21.

Service applicatif d'authentification. Reçoit des ports (interfaces) par injection.
Aucune dépendance SQLAlchemy directe — pur Python.

Remplace progressivement auth/service.py (backward compat conservée le temps
que les resolvers migrent via US 21.9).
"""

import uuid
from datetime import datetime, UTC, timedelta
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
from core.database.constants import UserRole
from modules.inventory.application.email_service import EmailService
from core.exceptions import ErrorCode, MichiException, UnauthenticatedException
from typing import cast, Any


@dataclass
class AuthResult:
    """Résultat d'une opération d'authentification."""
    token: JwtToken
    user_model: User
    mfa_required: bool = False
    mfa_token: Optional[str] = None


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
        email_service: Optional[EmailService] = None,
        billing_service=None,
    ) -> None:
        self._users = user_repo
        self._orgs = org_repo
        self._memberships = membership_repo
        self._hasher = password_hasher
        self._tokens = token_service
        self._email = email_service
        self._billing = billing_service

    async def login(self, email: str, password: str) -> AuthResult:
        """
        Authentifie par email + password.

        Raises:
            UnauthenticatedException: si email inconnu ou password incorrect.
        """
        from loguru import logger
        email = email.strip().lower()
        password = password.strip()
        
        user_model = await self._users.get_model_by_email(email)
        if not user_model:
            logger.warning(f"Login failure: user {email} not found")
            raise UnauthenticatedException("Invalid email or password")

        if not user_model.hashed_password:
            logger.warning(f"Login failure: user {email} has no password (Google only)")
            raise UnauthenticatedException("Compte Google-only — utilisez Google Login")

        from modules.auth.domain.value_objects import HashedPassword
        hashed = HashedPassword(cast(str, user_model.hashed_password))
        
        # Diagnostic logging (Temporary for Sprint 21 Debugging)
        if not self._hasher.verify(password, hashed):
            logger.warning(f"Login failure: password mismatch for {email}")
            raise UnauthenticatedException("Invalid email or password")

        # Org active : utiliser current ou première membership
        active_org_id = user_model.current_organization_id
        
        # Sprint 21 Fix: Garantir qu'une organisation est sélectionnée si elle existe
        if not active_org_id and user_model.organizations:
            active_org_id = user_model.organizations[0].organization_id
            user_model.current_organization_id = active_org_id
            from loguru import logger
            logger.info(f"Auto-selected organization {active_org_id} for user {user_model.email}")
            await self._users._db.flush()

        # Check for 2FA
        if user_model.two_factor_enabled:
            # Generate a temporary token for MFA step (valid for 5 mins)
            mfa_token = self._tokens.create_access_token(
                user_id=cast(uuid.UUID, user_model.id),
                org_id=None,
                email=cast(str, user_model.email),
                expires_delta=timedelta(minutes=5)
            )
            return AuthResult(token=JwtToken(""), user_model=user_model, mfa_required=True, mfa_token=mfa_token.value)

        token = self._tokens.create_access_token(
            user_id=cast(uuid.UUID, user_model.id),
            org_id=cast(Optional[uuid.UUID], active_org_id),
            email=cast(str, user_model.email),
        )
        return AuthResult(token=token, user_model=user_model)

    async def verify_email(self, token: str) -> bool:
        """Valide un jeton de vérification et marque l'email comme vérifié."""
        user = await self._users.get_by_verification_token(token)
        if not user:
            return False
            
        user.email_verified_at = cast(Any, datetime.now(UTC))
        user.verification_token = cast(Any, None) # Consommé
        
        await self._users.save(cast(UserEntity, user))
        await self._users._db.flush()
        return True

    async def resend_verification_email(self, email: str) -> bool:
        """Rénvoie un e-mail de vérification avec un nouveau token."""
        user = await self._users.get_model_by_email(email)
        if not user or user.email_verified_at:
            return False
            
        # Nouveau token pour plus de sécurité
        new_token = str(uuid.uuid4())
        user.verification_token = cast(Any, new_token)
        await self._users.save(cast(UserEntity, user))
        await self._users._db.flush()
        
        if self._email:
            from core.config.settings import settings
            verify_link = f"{settings.FRONTEND_URL}/verify-email?token={new_token}"
            from loguru import logger
            logger.info(f"[AuthService] Requesting verification email resend for {user.email}")
            await self._email.send_verification_email(cast(str, user.email), verify_link)
            
        return True

    async def register(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        create_default_org: bool = True,
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
        # Génération du token de vérification (ex: uuid)
        verification_token = str(uuid.uuid4())

        user_model = User(
            email=email.lower(),
            first_name=first_name,
            last_name=last_name,
            hashed_password=hashed.value,
            is_active=True,
            verification_token=verification_token,
            email_verified_at=None, # Non vérifié par défaut
            organizations=[],
        )
        await self._users.save(cast(UserEntity, user_model))

        # Envoi de l'email de vérification
        if self._email:
            from core.config.settings import settings
            # L'URL de vérification pointe vers le frontend qui appellera la mutation verifyEmail
            verify_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
            from loguru import logger
            logger.info(f"[AuthService] Requesting verification email for {email}")
            await self._email.send_verification_email(email, verify_link)

        if create_default_org:
            org_name = f"Michi de {first_name or email.split('@')[0]}"
            org_model = Organization(
                name=org_name,
                slug=f"org-{uuid.uuid4().hex[:8]}",
                plan="" # Force un plan vide pour obliger le passage par /pricing
            )
            from modules.auth.domain.entities import OrganizationEntity
            await self._orgs.save(cast(OrganizationEntity, org_model))

            member = OrganizationMember(
                user_id=user_model.id,
                organization_id=org_model.id,
                role=UserRole.OWNER,
            )
            from modules.auth.domain.entities import MembershipEntity
            await self._memberships.save(cast(MembershipEntity, member))
            user_model.current_organization_id = org_model.id
            
            # Si l'utilisateur a été invité, on pourrait auto-vérifier son email
            # mais par sécurité on garde la vérification par lien sauf si c'est une invitation de confiance.
            # Pour l'instant on laisse tel quel.

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
        
        # Explicit commit to ensure user is visible to immediate subsequent requests (e.g., onboarding)
        await self._users._db.commit()
        from loguru import logger
        logger.info(f">>> [DEBUG] REGISTERED USER ID: {user_model.id} (EMAIL: {user_model.email}) <<<")

        token = self._tokens.create_access_token(
            user_id=cast(uuid.UUID, user_model.id),
            org_id=cast(Optional[uuid.UUID], user_model.current_organization_id),
            email=cast(str, user_model.email),
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
        else:
            # Utilisateur trouvé par email : on lie le google_id s'il est manquant
            if not user_model.google_id:
                user_model.google_id = cast(Any, google_id)
                await self._users._db.flush()

        if not user_model:
            # Création
            user_model = User(
                email=email.lower(),
                first_name=first_name,
                last_name=last_name,
                google_id=google_id,
                email_verified_at=cast(Any, datetime.now(UTC)), # Google est une source fiable
                is_active=True
            )
            await self._users.save(cast(UserEntity, user_model))

            org_name = f"Michi de {first_name or email.split('@')[0]}"
            org_model = Organization(
                name=org_name,
                slug=f"org-{uuid.uuid4().hex[:8]}",
            )
            from modules.auth.domain.entities import OrganizationEntity
            await self._orgs.save(cast(OrganizationEntity, org_model))

            member = OrganizationMember(
                user_id=user_model.id,
                organization_id=org_model.id,
                role=UserRole.ADMIN,
            )
            from modules.auth.domain.entities import MembershipEntity
            await self._memberships.save(cast(MembershipEntity, member))
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
            user_id=cast(uuid.UUID, user_model.id),
            org_id=cast(Optional[uuid.UUID], user_model.current_organization_id),
            email=cast(str, user_model.email),
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
        if not self._hasher.verify(current_password, HashedPassword(cast(str, user_model.hashed_password))):
            raise MichiException(message="Mot de passe actuel incorrect", code=ErrorCode.UNAUTHENTICATED)
            
        new_hashed = self._hasher.hash(new_password)
        user_model.hashed_password = cast(Any, new_hashed.value)
        await self._users._db.flush()
        return True

    async def toggle_user_status(self, user_id: uuid.UUID, is_active: bool) -> Optional[UserEntity]:
        """Active ou désactive un utilisateur."""
        user_entity = await self._users.get_by_id(user_id)
        if not user_entity:
            return None
            
        user_entity.is_active = is_active
        return await self._users.update(user_entity)

    async def request_password_reset(self, email: str) -> bool:
        """
        Initie le workflow de réinitialisation de mot de passe.
        """
        from datetime import datetime, timedelta
        import secrets
        from modules.auth.infrastructure.persistence.models import PasswordResetToken
        from core.config import settings
        from loguru import logger

        email = email.strip().lower()
        user_model = await self._users.get_model_by_email(email)
        
        # Sécurité : on ne dit pas si l'email existe ou non (prévention énumération)
        if not user_model:
            logger.info(f"Password reset requested for unknown email: {email}")
            return True

        # Générer token sécurisé
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        
        # Enregistrer le token
        reset_token = PasswordResetToken(
            user_id=user_model.id,
            token=token,
            expires_at=expires_at
        )
        self._users._db.add(reset_token)
        await self._users._db.flush()
        
        # Envoyer l'email
        if self._email:
            # TODO: Utiliser l'URL de base configurée
            base_url = "http://localhost:3000" if settings.ENVIRONMENT == "development" else "https://app.michi.ai"
            # On détecte la locale de l'utilisateur (simplifié : fr par défaut)
            locale = user_model.preferences.get("language", "fr")
            reset_link = f"{base_url}/{locale}/reset-password?token={token}"
            
            await self._email.send_password_reset(email, reset_link)
            
        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Valide le token et change le mot de passe.
        """
        from datetime import datetime, UTC, timedelta
        from sqlalchemy import select
        from modules.auth.infrastructure.persistence.models import PasswordResetToken
        from loguru import logger

        # Rechercher le token
        result = await self._users._db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token)
        )
        reset_token = result.scalar_one_or_none()
        
        if not reset_token:
            logger.warning(f"Invalid reset token: {token}")
            return False
            
        if reset_token.expires_at < datetime.now(UTC):
            logger.warning(f"Expired reset token: {token}")
            await self._users._db.delete(reset_token)
            await self._users._db.commit()
            return False
            
        # Changer le mot de passe
        user_model = await self._users.get_model_by_id(cast(uuid.UUID, reset_token.user_id))
        if not user_model:
            return False
            
        new_hashed = self._hasher.hash(new_password)
        user_model.hashed_password = cast(Any, new_hashed.value)
        
        # Supprimer le token utilisé
        await self._users._db.delete(reset_token)
        await self._users._db.commit()
        
        logger.info(f"Password successfully reset for user: {user_model.email}")
        return True
