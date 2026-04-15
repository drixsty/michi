"""
Middleware JWT Authentication
Extrait et valide le token JWT de chaque requête
"""
from fastapi import Request
from core.config import settings
from core.exceptions import UnauthenticatedException, ForbiddenException
from jose import JWTError

from core.security import decode_access_token


async def get_current_user_from_token(request: Request) -> tuple[str | None, str | None, str | None]:
    """
    Extrait user_id, org_id et email du token JWT.
    
    Args:
        request: FastAPI Request
    
    Returns:
        Tuple (user_id, org_id, email) ou (None, None, None)
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None, None, None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, None, None
    
    token = parts[1]
    
    try:
        # Décoder le token
        payload = decode_access_token(token)
        
        user_id = payload.get("user_id")
        org_id = payload.get("org_id")
        email = payload.get("email")
        
        return user_id, org_id, email
    
    except JWTError:
        return None, None, None
