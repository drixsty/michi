from jose import JWTError, jwt
from typing import Dict, Any, Optional
from loguru import logger
import os
import httpx
from core.config.settings import settings

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token using settings.SECRET_KEY."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"[JWT] Decoding failed: {e}")
        raise e

async def get_dev_token_claims() -> Dict[str, Any]:
    """
    Fetch the first user and organization from the database to create a mock JWT.
    Used for local development/Stdio transport when no token is provided by client.
    """
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://michi:michi123@localhost:5432/michi_db")
    
    # Try using asyncpg to query user and organization
    try:
        import asyncpg
        # Replace asyncpg driver if needed
        clean_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        conn = await asyncpg.connect(clean_url)
        try:
            row = await conn.fetchrow(
                "SELECT id::text, current_organization_id::text, email FROM users LIMIT 1"
            )
            if row:
                return {
                    "user_id": row["id"],
                    "org_id": row["current_organization_id"],
                    "email": row["email"]
                }
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Could not connect to database for dev claims: {e}. Using hardcoded fallback.")
    
    # Hardcoded fallback if DB is not reachable
    return {
        "user_id": "00000000-0000-0000-0000-000000000000",
        "org_id": "00000000-0000-0000-0000-000000000000",
        "email": "dev@michi.com"
    }

async def generate_dev_jwt() -> str:
    """Generate a JWT token for development."""
    claims = await get_dev_token_claims()
    from datetime import datetime, timedelta, UTC
    to_encode = claims.copy()
    to_encode.update({
        "exp": datetime.now(UTC) + timedelta(days=1),
        "typ": "access"
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
