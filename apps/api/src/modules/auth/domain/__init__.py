"""
Domaine Auth — entités, value objects et ports (interfaces).
"""
from .entities import (
    UserEntity,
    OrganizationEntity,
    MembershipEntity,
    InvitationEntity,
    UserRole,
    InvitationStatus,
    OrgPlan,
    SubscriptionStatus,
)
from .value_objects import Email, HashedPassword, OrgSlug, JwtToken
from .ports import (
    IUserRepository,
    IOrganizationRepository,
    IMembershipRepository,
    IInvitationRepository,
    IPasswordHasher,
    ITokenService,
    IOAuthProvider,
)

__all__ = [
    "UserEntity",
    "OrganizationEntity",
    "MembershipEntity",
    "InvitationEntity",
    "UserRole",
    "InvitationStatus",
    "OrgPlan",
    "SubscriptionStatus",
    "Email",
    "HashedPassword",
    "OrgSlug",
    "JwtToken",
    "IUserRepository",
    "IOrganizationRepository",
    "IMembershipRepository",
    "IInvitationRepository",
    "IPasswordHasher",
    "ITokenService",
    "IOAuthProvider",
]
