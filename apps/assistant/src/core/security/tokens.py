from jose import JWTError, jwt
from core.config.settings import settings
from typing import Dict, Optional

def decode_access_token(token: str) -> Dict[str, str]:
    """Décode et valide un token JWT pour l'Assistant."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        from loguru import logger
        logger.error(f"[JWT] Decoding failed: {e}")
        raise e
