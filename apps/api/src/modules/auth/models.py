"""
Re-export layer for backward compatibility.
Implementation moved to src.modules.auth.infrastructure.persistence.models.
"""
from .infrastructure.persistence.models import (
    User, 
    Organization, 
    OrganizationMember, 
    UserRole, 
    Invitation
)

__all__ = [
    "User",
    "Organization",
    "OrganizationMember",
    "UserRole",
    "Invitation",
]
