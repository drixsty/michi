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
    Lève UnauthenticatedException si le token est présent mais invalide.
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None, None, None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        # Token malformé mais présent
        raise UnauthenticatedException("Format de jeton invalide (Bearer requis)")
    
    token = parts[1]
    
    try:
        # Décoder le token (lèvera JWTError si expiré ou invalide)
        payload = decode_access_token(token)
        
        user_id = payload.get("user_id")
        org_id = payload.get("org_id")
        email = payload.get("email")
        
        if not user_id:
            raise UnauthenticatedException("Jeton invalide : identifiant utilisateur manquant")
            
        return user_id, org_id, email
    
    except JWTError as e:
        # On capture spécifiquement les erreurs de signature/expiration
        error_msg = str(e)
        if "expired" in error_msg.lower():
            raise UnauthenticatedException("Votre session a expiré. Veuillez vous reconnecter.")
        raise UnauthenticatedException("Jeton d'accès invalide ou corrompu")
    except Exception:
        raise UnauthenticatedException("Erreur lors de la validation de l'identité")
