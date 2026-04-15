"""
Faux repositories en mémoire — tests unitaires Auth (Sprint 21).

Implémentent les Protocols du domaine sans aucune dépendance SQLAlchemy.
Chaque fake stocke les données dans un dict Python simple.
"""

from __future__ import annotations
from typing import Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from src.modules.auth.domain.entities import (
    InvitationEntity,
    MembershipEntity,
    OrganizationEntity,
    UserEntity,
    UserRole,
    InvitationStatus,
)
from src.modules.auth.domain.value_objects import Email, HashedPassword, OrgSlug, JwtToken
from src.modules.auth.infrastructure.persistence.models import Invitation


# ---------------------------------------------------------------------------
# Fake DB (remplace self._users._db.flush())
# ---------------------------------------------------------------------------

class FakeDb:
    """Simule la session SQLAlchemy pour flush(), commit(), etc."""

    def __init__(self) -> None:
        self.flush = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.add = MagicMock()
        self.refresh = AsyncMock()
        self.execute = AsyncMock()
        self.scalar = AsyncMock()
        self.scalars = AsyncMock()


# ---------------------------------------------------------------------------
# Fake User Repository
# ---------------------------------------------------------------------------

class FakeUserRepository:
    """Repository utilisateur in-memory."""

    def __init__(self) -> None:
        self._store: dict[UUID, UserEntity] = {}
        self._passwords: dict[UUID, str] = {}
        # Expose _db pour compatibilité avec AuthService (appelle self._users._db.flush())
        self._db = FakeDb()

    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]:
        return self._store.get(user_id)

    async def get_by_email(self, email: Email) -> Optional[UserEntity]:
        for user in self._store.values():
            if user.email.value == email.value:
                return user
        return None

    async def get_by_google_id(self, google_id: str) -> Optional[UserEntity]:
        for user in self._store.values():
            if user.google_id == google_id:
                return user
        return None

    async def save(self, user: UserEntity, hashed_password: Optional[HashedPassword] = None) -> UserEntity:
        self._store[user.id] = user
        if hashed_password:
            self._passwords[user.id] = hashed_password.value
        return user

    async def update(self, user: UserEntity) -> UserEntity:
        self._store[user.id] = user
        return user

    # Méthodes supplémentaires appelées par ApplicationAuthService
    # (couche service pas encore purement sur Protocol — leakage temporaire)

    async def get_model_by_email(self, email: str) -> Optional[_FakeUserModel]:
        for uid, user in self._store.items():
            if user.email.value == email:
                pwd = self._passwords.get(uid)
                return _FakeUserModel(user, pwd)
        return None

    async def get_model_by_id(self, user_id: UUID) -> Optional[_FakeUserModel]:
        user = self._store.get(user_id)
        if user is None:
            return None
        pwd = self._passwords.get(user_id)
        return _FakeUserModel(user, pwd)

    async def get_by_google_id(self, google_id: str) -> Optional[UserEntity]:  # type: ignore[override]
        for user in self._store.values():
            if user.google_id == google_id:
                return user
        return None

    def seed_user(
        self,
        user: UserEntity,
        plain_hashed_password: Optional[str] = None,
    ) -> None:
        """Helper pour pré-charger des données de test."""
        self._store[user.id] = user
        if plain_hashed_password:
            self._passwords[user.id] = plain_hashed_password


class _FakeUserModel:
    """
    Objet imitant le modèle SQLAlchemy User pour les méthodes de service
    qui manipulent encore les modèles ORM directement.
    """

    def __init__(self, entity: UserEntity, hashed_password: Optional[str]) -> None:
        self.id = entity.id
        self.email = entity.email.value
        self.first_name = entity.first_name
        self.last_name = entity.last_name
        self.hashed_password = hashed_password
        self.google_id = entity.google_id
        self.current_organization_id = entity.current_organization_id
        self.is_active = entity.is_active
        self.organizations: list = []


# ---------------------------------------------------------------------------
# Fake Organization Repository
# ---------------------------------------------------------------------------

class FakeOrganizationRepository:
    """Repository organisation in-memory."""

    def __init__(self) -> None:
        self._store: dict[UUID, OrganizationEntity] = {}
        self._db = FakeDb()

    async def get_by_id(self, org_id: UUID) -> Optional[OrganizationEntity]:
        return self._store.get(org_id)

    async def get_by_slug(self, slug: OrgSlug) -> Optional[OrganizationEntity]:
        for org in self._store.values():
            if hasattr(org, "slug") and hasattr(org.slug, "value") and org.slug.value == slug.value:
                return org
        return None

    async def save(self, org: OrganizationEntity | object) -> OrganizationEntity | object:
        """Saves either an Entity or an ORM model (leakage) to the fake store."""
        if hasattr(org, "id"):
            self._store[org.id] = org # type: ignore
        return org

    async def list_for_user(self, user_id: UUID) -> list[OrganizationEntity]:
        return list(self._store.values())


# ---------------------------------------------------------------------------
# Fake Membership Repository
# ---------------------------------------------------------------------------

class FakeMembershipRepository:
    """Repository membership in-memory."""

    def __init__(self) -> None:
        self._store: dict[tuple[UUID, UUID], MembershipEntity] = {}
        self._db = FakeDb()

    async def get(self, org_id: UUID, user_id: UUID) -> Optional[MembershipEntity]:
        return self._store.get((org_id, user_id))

    async def save(self, membership: MembershipEntity) -> MembershipEntity:
        key = (membership.organization_id, membership.user_id)
        self._store[key] = membership
        return membership

    async def list_for_user(self, user_id: UUID) -> list[MembershipEntity]:
        return [m for m in self._store.values() if m.user_id == user_id]

    async def list_for_org(self, org_id: UUID) -> list[MembershipEntity]:
        return [m for m in self._store.values() if m.organization_id == org_id]

    async def delete(self, org_id: UUID, user_id: UUID) -> None:
        self._store.pop((org_id, user_id), None)


# ---------------------------------------------------------------------------
# Fake Invitation Repository
# ---------------------------------------------------------------------------

class FakeInvitationRepository:
    """Repository invitation in-memory."""

    def __init__(self) -> None:
        self._store: dict[str, InvitationEntity] = {}
        self._db = FakeDb()

    async def get_by_code(self, code: str) -> Optional[InvitationEntity]:
        return self._store.get(code)

    async def get_model_by_code(self, code: str) -> Optional[Invitation]:
        # On retourne l'entité qui se comporte assez comme un modèle pour les tests simples
        return self._store.get(code)  # type: ignore[return-value]

    async def save(self, invitation: InvitationEntity) -> InvitationEntity:
        self._store[invitation.code] = invitation
        return invitation

    async def update(self, invitation: InvitationEntity) -> InvitationEntity:
        self._store[invitation.code] = invitation
        return invitation

    async def list_for_org(self, org_id: UUID) -> list[InvitationEntity]:
        return [i for i in self._store.values() if i.organization_id == org_id]

    async def get_pending_invitation(self, email: str, org_id: UUID) -> Optional[InvitationEntity]:
        for i in self._store.values():
            if (i.email.lower() == email.strip().lower() 
                and i.organization_id == org_id 
                and i.status == InvitationStatus.PENDING):
                return i
        return None

    async def delete_invitation(self, invitation_id: UUID) -> None:
        to_delete = None
        for code, i in self._store.items():
            if hasattr(i, "id") and i.id == invitation_id:
                to_delete = code
                break
        if to_delete:
            self._store.pop(to_delete)


# ---------------------------------------------------------------------------
# Fake Password Hasher (déterministe pour les tests)
# ---------------------------------------------------------------------------

class FakePasswordHasher:
    """
    Hash factice — simplement préfixe 'hashed:'.
    Compatible avec IPasswordHasher.
    """

    _PREFIX = "$2b$12$"

    def hash(self, plain_password: str) -> HashedPassword:
        # On utilise le préfixe bcrypt pour que HashedPassword accepte la valeur
        fake_hash = f"$2b$12${'x' * 53}"
        return HashedPassword(fake_hash)

    def verify(self, plain_password: str, hashed: HashedPassword) -> bool:
        # Tout password "correct" == "secret123" dans les tests
        return plain_password == "secret123"


# ---------------------------------------------------------------------------
# Fake Token Service
# ---------------------------------------------------------------------------

_FAKE_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.fake"


class FakeTokenService:
    """
    Génère un JWT factice valide (3 segments).
    Compatible avec ITokenService.
    """

    def create_access_token(
        self,
        user_id: UUID,
        org_id: Optional[UUID],
        email: str,
    ) -> JwtToken:
        return JwtToken(_FAKE_JWT)

    def decode(self, token: JwtToken) -> dict:
        return {"user_id": "test", "email": "test@example.com"}
