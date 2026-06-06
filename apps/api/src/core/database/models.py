import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship

from core.database import Base, GUID
from .constants import UserRole, OrgPlan, SubscriptionStatus

class Organization(Base):
    """
    Organization Model: Parent entity grouping stores and users.
    Moved to Core for monorepo isolation.
    """
    __tablename__ = "organizations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Billing info
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    plan = Column(String(50), default="BASIC") # BASIC, PRO, ENTERPRISE
    subscription_status = Column(String(50), default="ACTIVE")
    trial_ends_at = Column(DateTime, nullable=True)
    
    # Onboarding Status
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_step = Column(String(50), default="welcome") # welcome, identity, connect, sync

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    settings = Column(JSON, server_default='{}', default={}, nullable=False) # Currency, etc.

    # Relationships (Using strings to decouple from specific module models)
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization {self.name}>"

class User(Base):
    """
    User Model: Fundamental identity.
    Moved to Core for monorepo isolation.
    """
    __tablename__ = "users"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    email_verified_at = Column(DateTime, nullable=True)
    verification_token = Column(String(255), nullable=True, index=True)

    current_organization_id = Column(GUID, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
    
    # 2FA Security
    two_factor_secret = Column(String(255), nullable=True) # Will store the encrypted TOTP secret
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    recovery_codes = Column(JSON, nullable=True) # Liste de codes hachés

    preferences = Column(JSON, default={}, nullable=False)
    
    # Relationships
    organizations = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

class OrganizationMember(Base):
    """
    OrganizationMember: Link table between User and Organization.
    Fundamental bridge moved to Core.
    """
    __tablename__ = "organization_members"

    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    permissions = Column(JSON, default={}, nullable=False)

    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organizations")


class SupportAuditLog(Base):
    """
    SupportAuditLog: Audit trail to log all support agent impersonation activities.
    """
    __tablename__ = "support_audit_logs"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    support_user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    impersonated_org_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    flow_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    # Relationships
    support_user = relationship("User", foreign_keys=[support_user_id])
    impersonated_org = relationship("Organization", foreign_keys=[impersonated_org_id])

    def __repr__(self):
        return f"<SupportAuditLog {self.support_user_id} -> {self.impersonated_org_id}: {self.action}>"


# Importer tous les autres modèles pour enregistrer les relations SQLAlchemy
# Ces imports doivent rester en bas pour éviter les imports circulaires
from modules.auth.infrastructure.persistence.models import Invitation  # noqa: F401, E402
from modules.inventory.infrastructure.persistence.models import (  # noqa: F401, E402
    Store, Product, Alert, SalesLog, Supplier, AlertEmail, PurchaseOrder
)
from modules.forecasting.infrastructure.persistence.models import (  # noqa: F401, E402
    CleanedDemand, Prediction
)
