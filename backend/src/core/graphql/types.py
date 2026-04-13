"""
Types GraphQL avec Strawberry
"""
import strawberry
from typing import Optional, List
from datetime import datetime
from uuid import UUID

@strawberry.type
class OrganizationType:
    """Type Organization GraphQL"""
    id: strawberry.ID
    name: str
    slug: str
    plan: str
    subscription_status: str
    created_at: datetime
    settings: str
    invitations: Optional[List['InvitationType']] = None

@strawberry.type
class OrganizationMemberType:
    """Type OrganizationMember GraphQL (Liaison User/Org)"""
    organization_id: strawberry.ID
    user_id: strawberry.ID
    role: str
    permissions: str # JSON string
    organization: Optional[OrganizationType] = None
    user: Optional['UserType'] = None

@strawberry.type
class UserType:
    """Type User GraphQL (SaaS Version)"""
    id: strawberry.ID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    current_organization_id: Optional[strawberry.ID] = None
    shop_id: Optional[strawberry.ID] = None
    created_at: datetime
    preferences: str
    
    # List of organizations the user belongs to
    organizations: List[OrganizationMemberType]

@strawberry.type
class StoreType:
    """Modèle Store (Anciennement SourceType)"""
    id: strawberry.ID
    name: str
    platform: str
    connected: bool
    last_sync_at: Optional[datetime] = None
    health_status: Optional[str] = "HEALTHY"
    organization_id: Optional[strawberry.ID] = None

@strawberry.type
class InvitationType:
    """Type Invitation GraphQL (SaaS)"""
    id: strawberry.ID
    email: str
    organization_id: strawberry.ID
    role: str
    status: str
    code: Optional[str] = None
    created_at: datetime
    expires_at: datetime

@strawberry.input
class LoginInput:
    """Input pour mutation login (SaaS)"""
    email: str
    password: str

@strawberry.input
class RegisterInput:
    """Input pour mutation register (Sprint 16)"""
    email: str
    password: str
    first_name: str
    last_name: str

@strawberry.input
class GoogleLoginInput:
    """Input pour authentification Google (SaaS)"""
    id_token: str

@strawberry.type
class AuthPayload:
    """Payload retourné par login"""
    token: str
    user: UserType

@strawberry.input
class UpdateProfileInput:
    """Input pour modification profil (US 11.2)"""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email_alerts_enabled: Optional[bool] = None
    min_severity: Optional[int] = None

@strawberry.input
class UpdateOrganizationInput:
    """Input pour modification organisation (Sprint 16 Relocation)"""
    name: Optional[str] = None
    currency: Optional[str] = None
    is_mutualized: Optional[bool] = None

@strawberry.input
class ChangePasswordInput:
    """Input pour modification de mot de passe"""
    current_password: str
    new_password: str

# SourceType alias for backward compatibility or refactor frontend
SourceType = StoreType
