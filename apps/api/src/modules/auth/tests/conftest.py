import uuid
from datetime import datetime

import pytest

# SQLAlchemy model imports to prevent "failed to locate a name" errors during mapper initialization
from src.modules.auth.models import User, Organization, OrganizationMember, Invitation
from src.modules.inventory.models import Store, Product, SalesLog, Supplier, Alert, PurchaseOrder, AlertEmail
from src.modules.forecasting.models import CleanedDemand, Prediction

from src.modules.auth.application.auth_service import ApplicationAuthService
from src.modules.auth.application.org_service import ApplicationOrgService
from src.modules.auth.domain.entities import UserEntity
from src.modules.auth.domain.value_objects import Email

from src.modules.auth.tests.fakes import (
    FakeInvitationRepository,
    FakeMembershipRepository,
    FakeOrganizationRepository,
    FakePasswordHasher,
    FakeTokenService,
    FakeUserRepository,
)


# ---------------------------------------------------------------------------
# Fixtures repositories
# ---------------------------------------------------------------------------

@pytest.fixture
def user_repo() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def org_repo() -> FakeOrganizationRepository:
    return FakeOrganizationRepository()


@pytest.fixture
def membership_repo() -> FakeMembershipRepository:
    return FakeMembershipRepository()


@pytest.fixture
def invitation_repo() -> FakeInvitationRepository:
    return FakeInvitationRepository()


@pytest.fixture
def password_hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def token_service() -> FakeTokenService:
    return FakeTokenService()


# ---------------------------------------------------------------------------
# Fixtures services
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_service(
    user_repo: FakeUserRepository,
    org_repo: FakeOrganizationRepository,
    membership_repo: FakeMembershipRepository,
    password_hasher: FakePasswordHasher,
    token_service: FakeTokenService,
) -> ApplicationAuthService:
    return ApplicationAuthService(
        user_repo=user_repo,  # type: ignore[arg-type]
        org_repo=org_repo,  # type: ignore[arg-type]
        membership_repo=membership_repo,  # type: ignore[arg-type]
        password_hasher=password_hasher,
        token_service=token_service,
    )


@pytest.fixture
def org_service(
    user_repo: FakeUserRepository,
    org_repo: FakeOrganizationRepository,
    membership_repo: FakeMembershipRepository,
    invitation_repo: FakeInvitationRepository,
    token_service: FakeTokenService,
) -> ApplicationOrgService:
    return ApplicationOrgService(
        user_repo=user_repo,  # type: ignore[arg-type]
        org_repo=org_repo,  # type: ignore[arg-type]
        membership_repo=membership_repo,  # type: ignore[arg-type]
        invitation_repo=invitation_repo,  # type: ignore[arg-type]
        token_service=token_service,
    )


# ---------------------------------------------------------------------------
# Fixtures données
# ---------------------------------------------------------------------------

@pytest.fixture
def existing_user(user_repo: FakeUserRepository) -> UserEntity:
    """Utilisateur pré-chargé avec password 'secret123' (FakePasswordHasher)."""
    user = UserEntity(
        id=uuid.uuid4(),
        email=Email("alice@michi.com"),
        first_name="Alice",
        last_name="Dupont",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    fake_hash = "$2b$12$" + "x" * 53  # hash factice accepté par HashedPassword
    user_repo.seed_user(user, plain_hashed_password=fake_hash)
    return user
