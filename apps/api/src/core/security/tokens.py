from datetime import datetime, UTC, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from core.config.settings import settings

# Durée de vie courte pour l'access token (configurée via env)
_ACCESS_EXPIRES = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

# Refresh token : 30 jours, rotation obligatoire à chaque usage
_REFRESH_EXPIRES = timedelta(days=30)

# Marqueur de type dans le payload — empêche la réutilisation croisée des tokens
_TYPE_ACCESS = "access"
_TYPE_REFRESH = "refresh"


def _get_write_key_and_algo() -> tuple[str, str]:
    if settings.ALGORITHM == "RS256" and settings.JWT_PRIVATE_KEY:
        return settings.JWT_PRIVATE_KEY, "RS256"
    return settings.SECRET_KEY, "HS256"


def _decode_token(token: str, expected_type: str) -> Dict[str, Any]:
    if settings.ALGORITHM == "RS256" and settings.JWT_PUBLIC_KEY:
        try:
            payload = jwt.decode(token, settings.JWT_PUBLIC_KEY, algorithms=["RS256"])
            if payload.get("typ") != expected_type:
                raise JWTError(f"Token type mismatch — expected {expected_type} token")
            return payload
        except JWTError as primary_err:
            if settings.JWT_OLD_PUBLIC_KEYS:
                old_keys = [k.strip() for k in settings.JWT_OLD_PUBLIC_KEYS.split(",") if k.strip()]
                for key in old_keys:
                    try:
                        payload = jwt.decode(token, key, algorithms=["RS256"])
                        if payload.get("typ") == expected_type:
                            return payload
                    except JWTError:
                        continue
            raise primary_err

    # Fallback sur HS256/SECRET_KEY
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    if payload.get("typ") != expected_type:
        raise JWTError(f"Token type mismatch — expected {expected_type} token")
    return payload


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Crée un access token JWT (courte durée)."""
    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.now(UTC) + (expires_delta or _ACCESS_EXPIRES),
        "typ": _TYPE_ACCESS,
    })
    key, algo = _get_write_key_and_algo()
    return jwt.encode(to_encode, key, algorithm=algo)


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
    key, algo = _get_write_key_and_algo()
    return jwt.encode(payload, key, algorithm=algo)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Décode et valide un access token. Lève JWTError si invalide ou expiré."""
    return _decode_token(token, _TYPE_ACCESS)


def decode_refresh_token(token: str) -> str:
    """
    Décode et valide un refresh token.
    Retourne le user_id ou lève JWTError.
    """
    payload = _decode_token(token, _TYPE_REFRESH)
    user_id = payload.get("sub")
    if not user_id:
        raise JWTError("Refresh token missing subject")
    return str(user_id)
