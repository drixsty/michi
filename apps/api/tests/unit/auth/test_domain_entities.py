"""
Tests Entités Domaine Auth — Sprint 21.

Teste UserEntity, OrganizationEntity, MembershipEntity, InvitationEntity.
Aucune dépendance externe — pure logique métier.
"""
import uuid
from datetime import datetime, timedelta


from src.modules.auth.domain.entities import (
    InvitationEntity,
    InvitationStatus,
    MembershipEntity,
    OrganizationEntity,
    OrgPlan,
    SubscriptionStatus,
    UserEntity,
    UserRole,
)
from src.modules.auth.domain.value_objects import Email, OrgSlug


# ---------------------------------------------------------------------------
# UserEntity
# ---------------------------------------------------------------------------

class TestUserEntity:
    def _make_user(self, **kwargs) -> UserEntity:
        defaults = dict(
            id=uuid.uuid4(),
            email=Email("user@example.com"),
            first_name="Jean",
            last_name="Dupont",
            is_active=True,
            created_at=datetime.utcnow(),
        )
        defaults.update(kwargs)
        return UserEntity(**defaults)

    def test_full_name_with_both_names(self) -> None:
        user = self._make_user(first_name="Jean", last_name="Dupont")
        assert user.full_name == "Jean Dupont"

    def test_full_name_first_only(self) -> None:
        user = self._make_user(first_name="Jean", last_name=None)
        assert user.full_name == "Jean"

    def test_full_name_fallback_to_email(self) -> None:
        user = self._make_user(first_name=None, last_name=None)
        assert user.full_name == "user@example.com"

    def test_has_google_auth_true(self) -> None:
        user = self._make_user(google_id="google-123")
        assert user.has_google_auth is True

    def test_has_google_auth_false(self) -> None:
        user = self._make_user(google_id=None)
        assert user.has_google_auth is False

    def test_deactivate(self) -> None:
        user = self._make_user(is_active=True)
        user.deactivate()
        assert user.is_active is False

    def test_switch_organization(self) -> None:
        user = self._make_user()
        new_org_id = uuid.uuid4()
        user.switch_organization(new_org_id)
        assert user.current_organization_id == new_org_id


# ---------------------------------------------------------------------------
# OrganizationEntity
# ---------------------------------------------------------------------------

class TestOrganizationEntity:
    def _make_org(self, **kwargs) -> OrganizationEntity:
        defaults = dict(
            id=uuid.uuid4(),
            name="Michi Corp",
            slug=OrgSlug("michi-corp"),
            plan=OrgPlan.BASIC,
            subscription_status=SubscriptionStatus.ACTIVE,
            created_at=datetime.utcnow(),
        )
        defaults.update(kwargs)
        return OrganizationEntity(**defaults)

    def test_is_active_subscription_active(self) -> None:
        org = self._make_org(subscription_status=SubscriptionStatus.ACTIVE)
        assert org.is_active_subscription is True

    def test_is_active_subscription_trialing(self) -> None:
        org = self._make_org(subscription_status=SubscriptionStatus.TRIALING)
        assert org.is_active_subscription is True

    def test_is_active_subscription_canceled(self) -> None:
        org = self._make_org(subscription_status=SubscriptionStatus.CANCELED)
        assert org.is_active_subscription is False

    def test_currency_default(self) -> None:
        org = self._make_org()
        assert org.currency == "€"

    def test_currency_custom(self) -> None:
        org = self._make_org(settings={"currency": "$"})
        assert org.currency == "$"

    def test_is_mutualized_false_by_default(self) -> None:
        org = self._make_org()
        assert org.is_mutualized is False

    def test_is_mutualized_true(self) -> None:
        org = self._make_org(settings={"is_mutualized": True})
        assert org.is_mutualized is True


# ---------------------------------------------------------------------------
# MembershipEntity
# ---------------------------------------------------------------------------

class TestMembershipEntity:
    def _make_membership(self, role: UserRole = UserRole.VIEWER, **kwargs) -> MembershipEntity:
        defaults = dict(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role=role,
        )
        defaults.update(kwargs)
        return MembershipEntity(**defaults)

    def test_admin_can_all(self) -> None:
        m = self._make_membership(role=UserRole.ADMIN)
        assert m.can("delete_product") is True
        assert m.can("anything") is True

    def test_viewer_denied_by_default(self) -> None:
        m = self._make_membership(role=UserRole.VIEWER)
        assert m.can("delete_product") is False

    def test_viewer_with_explicit_permission(self) -> None:
        m = self._make_membership(
            role=UserRole.VIEWER,
            permissions={"view_dashboard": True}
        )
        assert m.can("view_dashboard") is True
        assert m.can("delete_product") is False


# ---------------------------------------------------------------------------
# InvitationEntity
# ---------------------------------------------------------------------------

class TestInvitationEntity:
    def _make_invitation(self, days_offset: int = 7, status: InvitationStatus = InvitationStatus.PENDING) -> InvitationEntity:
        now = datetime.utcnow()
        return InvitationEntity(
            id=uuid.uuid4(),
            email=Email("invite@example.com"),
            organization_id=uuid.uuid4(),
            role=UserRole.VIEWER,
            code="abc123",
            status=status,
            created_at=now,
            expires_at=now + timedelta(days=days_offset),
        )

    def test_is_not_expired_future(self) -> None:
        inv = self._make_invitation(days_offset=7)
        assert inv.is_expired is False

    def test_is_expired_past(self) -> None:
        inv = self._make_invitation(days_offset=-1)
        assert inv.is_expired is True

    def test_is_usable_pending_and_not_expired(self) -> None:
        inv = self._make_invitation(days_offset=7, status=InvitationStatus.PENDING)
        assert inv.is_usable is True

    def test_is_not_usable_expired(self) -> None:
        inv = self._make_invitation(days_offset=-1, status=InvitationStatus.PENDING)
        assert inv.is_usable is False

    def test_is_not_usable_accepted(self) -> None:
        inv = self._make_invitation(days_offset=7, status=InvitationStatus.ACCEPTED)
        assert inv.is_usable is False
