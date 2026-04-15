"""
Tests ApplicationAuthService — Sprint 21 (DDD Hexagonal).

Teste la couche Application avec de faux repositories in-memory.
Aucun accès DB, aucune dépendance SQLAlchemy.
"""
import uuid
from datetime import datetime

import pytest

from src.modules.auth.application.auth_service import ApplicationAuthService
from src.modules.auth.domain.entities import UserEntity
from src.modules.auth.domain.value_objects import Email
from exceptions import MichiException, UnauthenticatedException

from tests.unit.auth.fakes import (
    FakeMembershipRepository,
    FakeOrganizationRepository,
    FakePasswordHasher,
    FakeTokenService,
    FakeUserRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_auth_service(user_repo=None, org_repo=None, membership_repo=None):
    return ApplicationAuthService(
        user_repo=user_repo or FakeUserRepository(),
        org_repo=org_repo or FakeOrganizationRepository(),
        membership_repo=membership_repo or FakeMembershipRepository(),
        password_hasher=FakePasswordHasher(),
        token_service=FakeTokenService(),
    )


def _seed_user(user_repo: FakeUserRepository, email: str = "alice@michi.com") -> UserEntity:
    user = UserEntity(
        id=uuid.uuid4(),
        email=Email(email),
        first_name="Alice",
        last_name="Dupont",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    fake_hash = "$2b$12$" + "x" * 53
    user_repo.seed_user(user, plain_hashed_password=fake_hash)
    return user


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success() -> None:
    user_repo = FakeUserRepository()
    _seed_user(user_repo)
    service = _make_auth_service(user_repo=user_repo)

    result = await service.login("alice@michi.com", "secret123")

    assert result.token.value.count(".") == 2
    assert result.user_model.email == "alice@michi.com"


@pytest.mark.asyncio
async def test_login_unknown_email_raises() -> None:
    service = _make_auth_service()
    with pytest.raises(UnauthenticatedException):
        await service.login("nobody@michi.com", "secret123")


@pytest.mark.asyncio
async def test_login_wrong_password_raises() -> None:
    user_repo = FakeUserRepository()
    _seed_user(user_repo)
    service = _make_auth_service(user_repo=user_repo)  # noqa

    with pytest.raises(UnauthenticatedException):
        await service.login("alice@michi.com", "wrongpassword")


@pytest.mark.asyncio
async def test_login_google_only_account_raises() -> None:
    """Compte Google-only (pas de hashed_password) ne peut pas se connecter par email."""
    user_repo = FakeUserRepository()
    google_user = UserEntity(
        id=uuid.uuid4(),
        email=Email("google@michi.com"),
        first_name="Google",
        last_name="User",
        is_active=True,
        created_at=datetime.utcnow(),
        google_id="google-abc",
    )
    user_repo.seed_user(google_user, plain_hashed_password=None)
    service = _make_auth_service(user_repo=user_repo)

    with pytest.raises(UnauthenticatedException):
        await service.login("google@michi.com", "any_password")


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_new_user() -> None:
    service = _make_auth_service()

    result = await service.register(
        email="bob@michi.com",
        password="password123",
        first_name="Bob",
        last_name="Martin",
    )

    assert result.token.value.count(".") == 2
    assert result.user_model.email == "bob@michi.com"


@pytest.mark.asyncio
async def test_register_normalizes_email() -> None:
    service = _make_auth_service()

    result = await service.register(
        email="  BOB@MICHI.COM  ",
        password="password123",
        first_name="Bob",
        last_name="Martin",
    )

    assert result.user_model.email == "bob@michi.com"


@pytest.mark.asyncio
async def test_register_duplicate_email_raises() -> None:
    user_repo = FakeUserRepository()
    _seed_user(user_repo, email="alice@michi.com")
    service = _make_auth_service(user_repo=user_repo)

    with pytest.raises(MichiException):
        await service.register(
            email="alice@michi.com",
            password="newpassword",
            first_name="Alice",
            last_name="Clone",
        )


@pytest.mark.asyncio
async def test_register_new_user_has_no_org() -> None:
    service = _make_auth_service()

    result = await service.register(
        email="charlie@michi.com",
        password="pass",
        first_name="Charlie",
        last_name="Brown",
    )
    assert result.user_model.current_organization_id is None


# ---------------------------------------------------------------------------
# get_user_by_id()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_existing_user() -> None:
    user_repo = FakeUserRepository()
    user = _seed_user(user_repo)
    service = _make_auth_service(user_repo=user_repo)

    result = await service.get_user_by_id(user.id)
    assert result is not None
    assert result.id == user.id
    assert result.email.value == "alice@michi.com"


@pytest.mark.asyncio
async def test_get_unknown_user_returns_none() -> None:
    service = _make_auth_service()
    result = await service.get_user_by_id(uuid.uuid4())
    assert result is None


# ---------------------------------------------------------------------------
# update_user()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_first_name() -> None:
    user_repo = FakeUserRepository()
    user = _seed_user(user_repo)
    service = _make_auth_service(user_repo=user_repo)

    result = await service.update_user(user.id, first_name="Alicia")
    assert result is not None
    assert result.first_name == "Alicia"


@pytest.mark.asyncio
async def test_update_unknown_user_returns_none() -> None:
    service = _make_auth_service()
    result = await service.update_user(uuid.uuid4(), first_name="Ghost")
    assert result is None


@pytest.mark.asyncio
async def test_toggle_user_status_deactivate() -> None:
    user_repo = FakeUserRepository()
    user = _seed_user(user_repo)
    service = _make_auth_service(user_repo=user_repo)

    result = await service.toggle_user_status(user.id, is_active=False)
    assert result is not None
    assert result.is_active is False
