"""
AuthService : Business logic pour authentification
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict

from .models import User
from .schemas import LoginInput, UserSchema, AuthPayload
from src.core.security import verify_password, create_access_token
from src.core.exceptions import UnauthenticatedException


class AuthService:
    """Service d'authentification"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def login(self, input_data: LoginInput) -> AuthPayload:
        """
        Authentifie un utilisateur et retourne un token JWT.
        
        Args:
            input_data: Email + password
        
        Returns:
            AuthPayload avec token et user
        
        Raises:
            UnauthenticatedException: Si credentials invalides
        """
        # Récupérer user par email
        user = await self._get_user_by_email(input_data.email)
        
        if not user:
            raise UnauthenticatedException("Invalid email or password")
        
        # Vérifier password
        if not verify_password(input_data.password, user.hashed_password):
            raise UnauthenticatedException("Invalid email or password")
        
        # Créer token JWT
        token_data = {
            "user_id": str(user.id),
            "shop_id": str(user.shop_id),
            "email": user.email
        }
        
        token = create_access_token(token_data)
        
        # Retourner payload
        return AuthPayload(
            token=token,
            user=UserSchema.model_validate(user)
        )
    
    async def _get_user_by_email(self, email: str) -> User | None:
        """Récupère un user par email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> User | None:
        """Récupère un user par ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
