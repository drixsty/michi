"""
Tests ApplicationOrgService — Sprint 21 (DDD Hexagonal).

Teste la couche Application avec de faux repositories in-memory.
Aucun accès DB, aucune dépendance SQLAlchemy.
"""
from __future__ import annotations

import uuid
from datetime import datetime

import pytest

from src.modules.auth.application.org_service import ApplicationOrgService
from src.modules.auth.domain.entities import UserEntity
from src.modules.auth.domain.value_objects import Email
from michi_core.exceptions import MichiException

from src.modules.auth.tests.fakes import (
    FakeInvitationRepository,
    FakeMembershipRepository,
    FakeOrganizationRepository,
    FakeTokenService,
    FakeUserRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_org_service(user_repo=None, org_repo=None, membership_repo=None, invitation_repo=None):
    return ApplicationOrgService(
        user_repo=user_repo or FakeUserRepository(),
        org_repo=org_repo or FakeOrganizationRepository(),
        membership_repo=membership_repo or FakeMembershipRepository(),
        invitation_repo=invitation_repo or FakeInvitationRepository(),
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
    user_repo.seed_user(user, plain_hashed_password="$2b$12$" + "x" * 53)
    return user


# ---------------------------------------------------------------------------
# create_organization()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_organization_success() -> None:
    user_repo = FakeUserRepository()
    org_repo = FakeOrganizationRepository()
    membership_repo = FakeMembershipRepository()
    user = _seed_user(user_repo)
    service = _make_org_service(
        user_repo=user_repo,
        org_repo=org_repo,
        membership_repo=membership_repo
    )

    result = await service.create_organization(
        user_id=user.id,
        name="Ma Boutique",
        plan="BASIC"
    )

    assert result.org_model is not None
    assert result.org_model.name == "Ma Boutique"
    assert result.token.value.count(".") == 2


@pytest.mark.asyncio
async def test_create_organization_unknown_user_raises() -> None:
    service = _make_org_service()
    with pytest.raises(ValueError, match="introuvable"):
        await service.create_organization(user_id=uuid.uuid4(), name="Test")


@pytest.mark.asyncio
async def test_create_organization_adds_admin_membership() -> None:
    user_repo = FakeUserRepository()
    membership_repo = FakeMembershipRepository()
    user = _seed_user(user_repo)
    service = _make_org_service(user_repo=user_repo, membership_repo=membership_repo)

    result = await service.create_organization(user_id=user.id, name="Boutique")

    memberships = await membership_repo.list_for_org(result.org_model.id)
    assert len(memberships) == 1
    member = memberships[0]
    assert member.user_id == user.id


# ---------------------------------------------------------------------------
# switch_organization()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_switch_organization_success() -> None:
    user_repo = FakeUserRepository()
    org_repo = FakeOrganizationRepository()
    membership_repo = FakeMembershipRepository()
    user = _seed_user(user_repo)
    service = _make_org_service(
        user_repo=user_repo, org_repo=org_repo, membership_repo=membership_repo
    )

    # Créer une org manuellement
    result = await service.create_organization(user_id=user.id, name="Org A")
    org_id = result.org_model.id

    # Switch
    token, user_model = await service.switch_organization(
        user_id=user.id,
        organization_id=org_id
    )

    assert token.value.count(".") == 2
    assert user_model is not None


@pytest.mark.asyncio
async def test_switch_organization_unknown_user_raises() -> None:
    service = _make_org_service()
    with pytest.raises(ValueError):
        await service.switch_organization(
            user_id=uuid.uuid4(),
            organization_id=uuid.uuid4()
        )


# ---------------------------------------------------------------------------
# get_members()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_members_returns_empty_list_for_new_org() -> None:
    org_id = uuid.uuid4()
    membership_repo = FakeMembershipRepository()
    service = _make_org_service(membership_repo=membership_repo)

    members = await service.get_members(org_id)
    assert members == []


@pytest.mark.asyncio
async def test_get_members_after_add_returns_member() -> None:
    user_repo = FakeUserRepository()
    membership_repo = FakeMembershipRepository()
    user = _seed_user(user_repo)
    service = _make_org_service(user_repo=user_repo, membership_repo=membership_repo)

    result = await service.create_organization(user_id=user.id, name="TestOrg")
    members = await service.get_members(result.org_model.id)

    # Membership créé lors de create_organization
    assert len(members) >= 1


# ---------------------------------------------------------------------------
# create_invitation()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_invitation_success() -> None:
    invitation_repo = FakeInvitationRepository()
    service = _make_org_service(invitation_repo=invitation_repo)
    org_id = uuid.uuid4()

    from src.modules.auth.domain.entities import UserRole as DomainUserRole
    invitation = await service.create_invitation(
        email="bob@test.com",
        organization_id=org_id,
        role=DomainUserRole.VIEWER,
        invited_by_id=uuid.uuid4()
    )

    assert invitation is not None
    assert invitation.email == "bob@test.com"
    assert invitation.organization_id == org_id


@pytest.mark.asyncio
async def test_create_invitation_generates_code() -> None:
    invitation_repo = FakeInvitationRepository()
    service = _make_org_service(invitation_repo=invitation_repo)

    from src.modules.auth.domain.entities import UserRole as DomainUserRole
    invitation = await service.create_invitation(
        email="charlie@test.com",
        organization_id=uuid.uuid4(),
        role=DomainUserRole.VIEWER,
        invited_by_id=uuid.uuid4()
    )

    assert invitation.code is not None
    assert len(invitation.code) > 0


# ---------------------------------------------------------------------------
# accept_invitation()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_accept_invitation_success() -> None:
    user_repo = FakeUserRepository()
    invitation_repo = FakeInvitationRepository()
    membership_repo = FakeMembershipRepository()
    user = _seed_user(user_repo)
    service = _make_org_service(
        user_repo=user_repo,
        invitation_repo=invitation_repo,
        membership_repo=membership_repo
    )

    from src.modules.auth.domain.entities import UserRole as DomainUserRole
    invitation = await service.create_invitation(
        email="alice@michi.com",
        organization_id=uuid.uuid4(),
        role=DomainUserRole.VIEWER,
        invited_by_id=uuid.uuid4()
    )

    result = await service.accept_invitation(code=invitation.code, user_id=user.id)
    assert result is True


# ---------------------------------------------------------------------------
# remove_member()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_remove_member_success() -> None:
    user_repo = FakeUserRepository()
    membership_repo = FakeMembershipRepository()
    user = _seed_user(user_repo)
    service = _make_org_service(user_repo=user_repo, membership_repo=membership_repo)

    result = await service.create_organization(user_id=user.id, name="OrgB")
    org_id = result.org_model.id

    removed = await service.remove_member(org_id=org_id, user_id=user.id)
    assert removed is True

    members_after = await service.get_members(org_id)
    assert len(members_after) == 0
