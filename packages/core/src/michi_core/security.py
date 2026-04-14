"""
Sécurité : JWT tokens et password hashing
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# Context pour hashing passwords (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash un password avec bcrypt.
    
    Args:
        password: Password en clair
    
    Returns:
        Password hashé
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie un password contre son hash.
    
    Args:
        plain_password: Password en clair
        hashed_password: Password hashé
    
    Returns:
        True si match, False sinon
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crée un token JWT.
    
    Args:
        data: Payload du token (user_id, shop_id, etc.)
        expires_delta: Durée de validité (défaut: settings.ACCESS_TOKEN_EXPIRE_HOURS)
    
    Returns:
        Token JWT encodé
    
    Example:
        >>> token = create_access_token({"user_id": "123", "shop_id": "456"})
        >>> # Token valide 24h
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, str]:
    """
    Décode et valide un token JWT.
    
    Args:
        token: Token JWT à décoder
    
    Returns:
        Payload du token
    
    Raises:
        JWTError: Si token invalide ou expiré
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise e
