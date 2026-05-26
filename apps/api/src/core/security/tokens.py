from datetime import datetime, UTC, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from core.config.settings import settings

# Durée de vie courte pour l'access token (configurée via env)
_ACCESS_EXPIRES = timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

# Refresh token : 30 jours, rotation obligatoire à chaque usage
_REFRESH_EXPIRES = timedelta(days=30)

# Marqueur de type dans le payload — empêche la réutilisation croisée des tokens
_TYPE_ACCESS = "access"
_TYPE_REFRESH = "refresh"


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crée un access token JWT (courte durée)."""
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.now(UTC) + (expires_delta or _ACCESS_EXPIRES),
        "typ": _TYPE_ACCESS,
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Crée un refresh token JWT (longue durée, 30 jours).
    Contient uniquement user_id — pas de org_id ni d'email pour minimiser la surface.
    """
    payload = {
        "sub": user_id,
        "exp": datetime.now(UTC) + _REFRESH_EXPIRES,
        "typ": _TYPE_REFRESH,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Décode et valide un access token. Lève JWTError si invalide ou expiré."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("typ") != _TYPE_ACCESS:
        raise JWTError("Token type mismatch — expected access token")
    return payload


def decode_refresh_token(token: str) -> str:
    """
    Décode et valide un refresh token.
    Retourne le user_id ou lève JWTError.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("typ") != _TYPE_REFRESH:
        raise JWTError("Token type mismatch — expected refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise JWTError("Refresh token missing subject")
    return str(user_id)
