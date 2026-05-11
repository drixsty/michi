from core.database.models import Organization, User, OrganizationMember
"""
Adaptateurs sécurité Auth — Sprint 21.

Implémentations concrètes des ports IPasswordHasher et ITokenService.
Délèguent à core.security (bcrypt, JWT).
"""

from core.config import settings
from typing import Optional
from uuid import UUID

from core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from modules.auth.domain.value_objects import HashedPassword, JwtToken


class BcryptPasswordHasher:
    """Implémente IPasswordHasher via bcrypt (core.security)."""

    def hash(self, plain_password: str) -> HashedPassword:
        hashed = hash_password(plain_password)
        return HashedPassword(hashed)

    def verify(self, plain_password: str, hashed: HashedPassword) -> bool:
        return verify_password(plain_password, hashed.value)


class JwtTokenService:
    """Implémente ITokenService via python-jose (core.security)."""

    def create_access_token(
        self,
        user_id: UUID,
        org_id: Optional[UUID],
        email: str,
    ) -> JwtToken:
        token_data: dict[str, str] = {
            "user_id": str(user_id),
            "email": email,
        }
        if org_id is not None:
            token_data["org_id"] = str(org_id)
        raw = create_access_token(token_data)
        return JwtToken(raw)

    def decode(self, token: JwtToken) -> dict:
        from core.security import decode_access_token
        return decode_access_token(token.value)
