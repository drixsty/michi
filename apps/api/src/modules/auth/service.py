"""
AuthService : Business logic pour authentification
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Dict, List, Optional
import uuid

from .models import User, Organization, OrganizationMember, UserRole
from .schemas import LoginInput, UserSchema, AuthPayload
from src.core.security import verify_password, hash_password, create_access_token
from src.core.exceptions import UnauthenticatedException, MichiException, ErrorCode


class AuthService:
    """Service d'authentification"""
    
    def __init__(self, db: AsyncSession, billing_service=None):
        self.db = db
        self.billing = billing_service
    
    async def login(self, input_data: LoginInput) -> AuthPayload:
        """
        Authentifie un utilisateur et retourne un token JWT.
        """
        # Récupérer user par email avec ses organisations
        user = await self._get_user_with_orgs(input_data.email)
        
        if not user:
            raise UnauthenticatedException("Invalid email or password")
        
        # Vérifier password
        if not verify_password(input_data.password, user.hashed_password):
            raise UnauthenticatedException("Invalid email or password")
        
        # Déterminer l'organisation active (US 16.3)
        active_org_id = user.current_organization_id
        if not active_org_id and user.organizations:
            active_org_id = user.organizations[0].organization_id
            user.current_organization_id = active_org_id
            await self.db.flush()

        # Créer token JWT
        token_data = {
            "user_id": str(user.id),
            "org_id": str(active_org_id) if active_org_id else None,
            "email": user.email
        }
        
        token = create_access_token(token_data)
        
        # Retourner payload
        return AuthPayload(
            token=token,
            user=UserSchema.model_validate(user)
        )
    
    async def register(self, email: str, password: str, first_name: str, last_name: str) -> AuthPayload:
        """
        Crée un nouveau compte utilisateur sans organisation associée.
        L'onboarding (création d'org) sera géré dans une étape suivante.
        """
        email = email.strip().lower()
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = await self._get_user_with_orgs(email)
        if existing_user:
            raise MichiException(message="Cet email est déjà utilisé", code=ErrorCode.ALREADY_MEMBER)
            
        # Créer l'utilisateur
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            hashed_password=hash_password(password)
        )
        self.db.add(user)
        await self.db.flush()
        
        # NOTE: La création d'organisation est déportée vers le flux d'onboarding (US 19.4)
        
        # Initialiser explicitement les relations pour éviter MissingGreenlet lors de la sérialisation Pydantic
        user.organizations = []
        
        # Générer token sans org_id
        token_data = {
            "user_id": str(user.id),
            "org_id": None,
            "email": user.email
        }
        token = create_access_token(token_data)
        
        return AuthPayload(token=token, user=UserSchema.model_validate(user))

    async def login_with_google(self, google_id: str, email: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> AuthPayload:
        """
        Authentification via Google OAuth2 (US 16.2).
        """
        from sqlalchemy import func
        email = email.strip().lower()

        # Rechercher user par google_id ou email
        result = await self.db.execute(
            select(User).where((User.google_id == google_id) | (func.lower(User.email) == email))
            .options(selectinload(User.organizations).selectinload(OrganizationMember.organization))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Création auto du compte (onboarding)
            user = User(
                email=email,
                google_id=google_id,
                first_name=first_name,
                last_name=last_name,
                hashed_password=None # Pas de password local
            )
            self.db.add(user)
            await self.db.flush()
            
            # Créer organisation par défaut (US 16.1)
            org_name = f"Michi de {first_name or email.split('@')[0]}"
            org = Organization(name=org_name, slug=f"org-{uuid.uuid4().hex[:8]}")
            self.db.add(org)
            await self.db.flush()
            
            member = OrganizationMember(user_id=user.id, organization_id=org.id, role=UserRole.ADMIN)
            self.db.add(member)
            user.current_organization_id = org.id
            await self.db.flush()
            
            # Sync Stripe Customer (US 17.1)
            if self.billing:
                stripe_id = await self.billing.create_customer(
                    name=org.name, 
                    email=user.email, 
                    org_id=str(org.id)
                )
                if stripe_id:
                    org.stripe_customer_id = stripe_id
                    await self.db.flush()

        # Générer token
        token_data = {
            "user_id": str(user.id),
            "org_id": str(user.current_organization_id),
            "email": user.email
        }
        token = create_access_token(token_data)
        
        return AuthPayload(token=token, user=UserSchema.model_validate(user))

    async def _get_user_with_orgs(self, email: str) -> Optional[User]:
        """Récupère un user avec ses relations d'organisation."""
        from sqlalchemy import func
        email = email.strip().lower()
        result = await self.db.execute(
            select(User).where(func.lower(User.email) == email)
            .options(selectinload(User.organizations).selectinload(OrganizationMember.organization))
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Récupère un user par ID avec orgs."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
            .options(selectinload(User.organizations).selectinload(OrganizationMember.organization))
        )
        return result.scalar_one_or_none()

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Met à jour un utilisateur"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        await self.db.flush()
        return user

    async def remove_member(self, organization_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Supprime un membre de l'organisation."""
        from sqlalchemy import delete
        await self.db.execute(
            delete(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id
            )
        )
        return True

    async def update_member_role(self, organization_id: uuid.UUID, user_id: uuid.UUID, role: UserRole) -> Optional[OrganizationMember]:
        """Met à jour le rôle d'un membre."""
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        if member:
            member.role = role
            await self.db.flush()
        return member

    async def toggle_user_status(self, user_id: uuid.UUID, is_active: bool) -> Optional[User]:
        """Active ou désactive un compte utilisateur (Bannissement)."""
        user = await self.get_user_by_id(str(user_id))
        if user:
            user.is_active = is_active
            await self.db.flush()
        return user
