"""
Middleware JWT Authentication
Extrait et valide le token JWT de chaque requête
"""
from fastapi import Request
from jose import JWTError

from src.core.security import decode_access_token


async def get_current_user_from_token(request: Request) -> tuple[str | None, str | None]:
    """
    Extrait user_id et org_id du token JWT.
    
    Args:
        request: FastAPI Request
    
    Returns:
        Tuple (user_id, org_id) ou (None, None)
    """
    # ... (header extraction logic same)
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None, None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, None
    
    token = parts[1]
    
    try:
        # Décoder le token
        payload = decode_access_token(token)
        
        user_id = payload.get("user_id")
        org_id = payload.get("org_id")
        
        return user_id, org_id
    
    except JWTError:
        return None, None
