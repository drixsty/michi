"""
Ports du domaine Auth — Sprint 21.

Interfaces (Protocol) que les adaptateurs infrastructure implémentent.
Aucune dépendance externe — pure abstraction Python.
"""

from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    InvitationEntity,
    MembershipEntity,
    OrganizationEntity,
    UserEntity,
    UserRole,
)
from .value_objects import Email, HashedPassword, JwtToken, OrgSlug


@runtime_checkable
class IUserRepository(Protocol):
    """Port de persistance utilisateurs."""

    async def get_by_id(self, user_id: UUID) -> Optional[UserEntity]: ...

    async def get_by_email(self, email: Email) -> Optional[UserEntity]: ...

    async def get_by_google_id(self, google_id: str) -> Optional[UserEntity]: ...

    async def save(self, user: UserEntity, hashed_password: Optional[HashedPassword] = None) -> UserEntity: ...

    async def update(self, user: UserEntity) -> UserEntity: ...

    async def get_model_by_email(self, email: str) -> Optional[object]: ...


@runtime_checkable
class IOrganizationRepository(Protocol):
    """Port de persistance organisations."""

    async def get_by_id(self, org_id: UUID) -> Optional[OrganizationEntity]: ...

    async def get_by_slug(self, slug: OrgSlug) -> Optional[OrganizationEntity]: ...

    async def save(self, org: OrganizationEntity) -> OrganizationEntity: ...

    async def list_for_user(self, user_id: UUID) -> list[OrganizationEntity]: ...


@runtime_checkable
class IMembershipRepository(Protocol):
    """Port de persistance memberships."""

    async def get(self, org_id: UUID, user_id: UUID) -> Optional[MembershipEntity]: ...

    async def save(self, membership: MembershipEntity) -> MembershipEntity: ...

    async def list_for_user(self, user_id: UUID) -> list[MembershipEntity]: ...

    async def list_for_org(self, org_id: UUID) -> list[MembershipEntity]: ...

    async def delete(self, org_id: UUID, user_id: UUID) -> None: ...


@runtime_checkable
class IInvitationRepository(Protocol):
    """Port de persistance invitations."""

    async def get_by_code(self, code: str) -> Optional[InvitationEntity]: ...

    async def save(self, invitation: InvitationEntity) -> InvitationEntity: ...

    async def update(self, invitation: InvitationEntity) -> InvitationEntity: ...

    async def list_for_org(self, org_id: UUID) -> list[InvitationEntity]: ...

    async def get_pending_invitation(self, email: str, org_id: UUID) -> Optional[InvitationEntity]: ...

    async def delete_invitation(self, invitation_id: UUID) -> None: ...


@runtime_checkable
class IPasswordHasher(Protocol):
    """Port de hachage de mot de passe (bcrypt)."""

    def hash(self, plain_password: str) -> HashedPassword: ...

    def verify(self, plain_password: str, hashed: HashedPassword) -> bool: ...


@runtime_checkable
class ITokenService(Protocol):
    """Port de génération et validation de tokens JWT."""

    def create_access_token(self, user_id: UUID, org_id: Optional[UUID], email: str) -> JwtToken: ...

    def decode(self, token: JwtToken) -> dict: ...


@runtime_checkable
class IOAuthProvider(Protocol):
    """Port d'intégration OAuth externe (Google, etc.)."""

    async def get_user_info(self, code: str) -> dict: ...
