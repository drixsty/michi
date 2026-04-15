"""
Mappers Infrastructure Auth — Sprint 21.

Fonctions de conversion SQLAlchemy model ↔ Domain entity.
Séparent explicitement la persistance du domaine.
"""

from typing import TYPE_CHECKING

from src.modules.auth.domain.entities import (
    InvitationEntity,
    InvitationStatus,
    MembershipEntity,
    OrgPlan,
    OrganizationEntity,
    SubscriptionStatus,
    UserEntity,
    UserRole,
)
from src.modules.auth.domain.value_objects import Email, OrgSlug

if TYPE_CHECKING:
    from .persistence.models import (
        Invitation,
        Organization,
        OrganizationMember,
        User,
    )


def user_to_entity(model: "User") -> UserEntity:
    return UserEntity(
        id=model.id,
        email=Email(model.email),
        first_name=model.first_name,
        last_name=model.last_name,
        is_active=model.is_active,
        created_at=model.created_at,
        google_id=model.google_id,
        current_organization_id=model.current_organization_id,
        preferences=model.preferences or {},
    )


def org_to_entity(model: "Organization") -> OrganizationEntity:
    plan = OrgPlan(model.plan) if model.plan else OrgPlan.BASIC
    status = (
        SubscriptionStatus(model.subscription_status)
        if model.subscription_status
        else SubscriptionStatus.ACTIVE
    )
    return OrganizationEntity(
        id=model.id,
        name=model.name,
        slug=OrgSlug(model.slug),
        plan=plan,
        subscription_status=status,
        created_at=model.created_at,
        stripe_customer_id=model.stripe_customer_id,
        settings=model.settings or {},
    )


def membership_to_entity(model: "OrganizationMember") -> MembershipEntity:
    from src.modules.auth.infrastructure.models import UserRole as ModelUserRole
    role_map = {
        ModelUserRole.ADMIN: UserRole.ADMIN,
        ModelUserRole.MANAGER: UserRole.MANAGER,
        ModelUserRole.VIEWER: UserRole.VIEWER,
    }
    return MembershipEntity(
        organization_id=model.organization_id,
        user_id=model.user_id,
        role=role_map.get(model.role, UserRole.VIEWER),
        permissions=model.permissions or {},
        joined_at=model.joined_at,
    )


def invitation_to_entity(model: "Invitation") -> InvitationEntity:
    from src.modules.auth.infrastructure.models import (
        InvitationStatus as ModelStatus,
        UserRole as ModelUserRole,
    )
    role_map = {
        ModelUserRole.ADMIN: UserRole.ADMIN,
        ModelUserRole.MANAGER: UserRole.MANAGER,
        ModelUserRole.VIEWER: UserRole.VIEWER,
    }
    status_map = {
        ModelStatus.PENDING: InvitationStatus.PENDING,
        ModelStatus.ACCEPTED: InvitationStatus.ACCEPTED,
        ModelStatus.EXPIRED: InvitationStatus.EXPIRED,
    }
    return InvitationEntity(
        id=model.id,
        email=Email(model.email),
        organization_id=model.organization_id,
        role=role_map.get(model.role, UserRole.VIEWER),
        code=model.code,
        status=status_map.get(model.status, InvitationStatus.PENDING),
        created_at=model.created_at,
        expires_at=model.expires_at,
        invited_by_id=model.invited_by_id,
    )
