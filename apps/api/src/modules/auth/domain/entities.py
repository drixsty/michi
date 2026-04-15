"""
Entités du domaine Auth — Sprint 21.

Entités avec identité propre. Ces classes sont des projections pures du domaine,
sans dépendance SQLAlchemy ni Pydantic. Elles reflètent le modèle métier Auth.
"""

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from .value_objects import Email, OrgSlug


from core.database.constants import UserRole, InvitationStatus, OrgPlan, SubscriptionStatus
from core.database.models import Organization, User, OrganizationMember

@dataclass
class UserEntity:
    """
    Entité utilisateur — projection domaine du modèle User SQLAlchemy.

    Immuable après construction (pas de setters publics exposés aux couches
    supérieures). Les modifications passent par les méthodes métier.
    """

    id: UUID
    email: Email
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    created_at: datetime
    google_id: Optional[str] = None
    current_organization_id: Optional[UUID] = None
    preferences: dict = field(default_factory=dict)

    @property
    def full_name(self) -> str:
        parts = filter(None, [self.first_name, self.last_name])
        return " ".join(parts) or self.email.value

    @property
    def has_google_auth(self) -> bool:
        return self.google_id is not None

    def deactivate(self) -> None:
        self.is_active = False

    def switch_organization(self, org_id: UUID) -> None:
        self.current_organization_id = org_id


@dataclass
class OrganizationEntity:
    """
    Entité organisation — projection domaine du modèle Organization SQLAlchemy.
    """

    id: UUID
    name: str
    slug: OrgSlug
    plan: OrgPlan
    subscription_status: SubscriptionStatus
    created_at: datetime
    stripe_customer_id: Optional[str] = None
    settings: dict = field(default_factory=dict)

    @property
    def is_active_subscription(self) -> bool:
        return self.subscription_status in (
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
        )

    @property
    def currency(self) -> str:
        return str(self.settings.get("currency", "€"))

    @property
    def is_mutualized(self) -> bool:
        return bool(self.settings.get("is_mutualized", False))


@dataclass(frozen=True)
class MembershipEntity:
    """
    Entité membership — lien User <-> Organization avec rôle et permissions.
    """

    organization_id: UUID
    user_id: UUID
    role: UserRole
    permissions: dict = field(default_factory=dict)
    joined_at: Optional[datetime] = None

    def can(self, permission: str) -> bool:
        """Vérifie un droit granulaire. Admin a tous les droits."""
        if self.role == UserRole.ADMIN:
            return True
        return bool(self.permissions.get(permission, False))


@dataclass(frozen=True)
class InvitationEntity:
    """
    Entité invitation — représente une invitation en attente pour un collaborateur.
    """

    id: UUID
    email: Email
    organization_id: UUID
    role: UserRole
    code: str
    status: InvitationStatus
    created_at: datetime
    expires_at: datetime
    invited_by_id: Optional[UUID] = None

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    @property
    def is_usable(self) -> bool:
        return self.status == InvitationStatus.PENDING and not self.is_expired
