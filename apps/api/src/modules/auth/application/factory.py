"""
Factory Auth — Sprint 21.

Construit les services applicatifs avec leurs dépendances injectées.
Point d'entrée unique pour obtenir un ApplicationAuthService ou ApplicationOrgService
depuis un AsyncSession.

Usage dans les resolvers :
    from src.modules.auth.application.factory import build_auth_service, build_org_service

    auth_svc = build_auth_service(info.context.db, info.context.billing)
    result = await auth_svc.login(email, password)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.infrastructure.repositories import (
    SQLAlchemyInvitationRepository,
    SQLAlchemyMembershipRepository,
    SQLAlchemyOrganizationRepository,
    SQLAlchemyUserRepository,
)
from src.modules.auth.infrastructure.security_adapters import (
    BCryptPasswordHasher,
    JwtTokenService,
)

from .auth_service import ApplicationAuthService
from .org_service import ApplicationOrgService


def build_auth_service(
    db: AsyncSession,
    billing_service=None,
) -> ApplicationAuthService:
    """Construit un ApplicationAuthService avec tous ses ports injectés."""
    user_repo = SQLAlchemyUserRepository(db)
    org_repo = SQLAlchemyOrganizationRepository(db)
    membership_repo = SQLAlchemyMembershipRepository(db)
    hasher = BCryptPasswordHasher()
    tokens = JwtTokenService()
    return ApplicationAuthService(
        user_repo=user_repo,
        org_repo=org_repo,
        membership_repo=membership_repo,
        password_hasher=hasher,
        token_service=tokens,
        billing_service=billing_service,
    )


def build_org_service(
    db: AsyncSession,
    billing_service=None,
) -> ApplicationOrgService:
    """Construit un ApplicationOrgService avec tous ses ports injectés."""
    user_repo = SQLAlchemyUserRepository(db)
    org_repo = SQLAlchemyOrganizationRepository(db)
    membership_repo = SQLAlchemyMembershipRepository(db)
    invitation_repo = SQLAlchemyInvitationRepository(db)
    tokens = JwtTokenService()
    return ApplicationOrgService(
        user_repo=user_repo,
        org_repo=org_repo,
        membership_repo=membership_repo,
        invitation_repo=invitation_repo,
        token_service=tokens,
        billing_service=billing_service,
    )
