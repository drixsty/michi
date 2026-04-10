"""
Types GraphQL avec Strawberry
"""
import strawberry
from typing import Optional
from datetime import datetime
from uuid import UUID


@strawberry.type
class UserType:
    """Type User GraphQL"""
    id: strawberry.ID
    email: str
    shop_id: strawberry.ID
    created_at: datetime
    preferences: str  # On retourne le JSON en string pour la simplicité MVP ou un type spécifique


@strawberry.input
class LoginInput:
    """Input pour mutation login"""
    email: str
    password: str


@strawberry.type
class AuthPayload:
    """Payload retourné par login"""
    token: str
    user: UserType

@strawberry.input
class UpdateProfileInput:
    """Input pour modification profil (US 11.2)"""
    email: Optional[str] = None
    email_alerts_enabled: Optional[bool] = None
    min_severity: Optional[int] = None
    currency: Optional[str] = None # Sprint 13
    is_mutualized: Optional[bool] = None # Sprint 13

@strawberry.input
class ChangePasswordInput:
    """Input pour modification de mot de passe"""
    current_password: str
    new_password: str

@strawberry.type
class SourceType:
    id: strawberry.ID
    name: str
    platform: str
    connected: bool
    last_sync_at: Optional[datetime] = None
    health_status: Optional[str] = "HEALTHY"
