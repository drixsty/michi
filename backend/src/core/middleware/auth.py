"""
Middleware JWT Authentication
Extrait et valide le token JWT de chaque requête
"""
from fastapi import Request
from jose import JWTError

from src.core.security import decode_access_token


async def get_current_user_from_token(request: Request) -> tuple[str | None, str | None]:
    """
    Extrait user_id et shop_id du token JWT.
    
    Args:
        request: FastAPI Request
    
    Returns:
        Tuple (user_id, shop_id) ou (None, None) si pas de token
    """
    # Récupérer le header Authorization
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        return None, None
    
    # Format attendu : "Bearer <token>"
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, None
    
    token = parts[1]
    
    try:
        # Décoder le token
        payload = decode_access_token(token)
        
        user_id = payload.get("user_id")
        shop_id = payload.get("shop_id")
        
        return user_id, shop_id
    
    except JWTError:
        # Token invalide ou expiré
        return None, None
