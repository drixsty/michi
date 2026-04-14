import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean, Uuid, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from michi_core.database import Base, GUID

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"

class InvitationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class Organization(Base):
    """
    Organization Model: Parent entity grouping stores and users.
    """
    __tablename__ = "organizations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Billing (Sprint 17/18)
    stripe_customer_id = Column(String(255), nullable=True)
    plan = Column(String(50), default="BASIC") # BASIC, PRO, ENTERPRISE
    subscription_status = Column(String(50), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    settings = Column(JSON, server_default='{}', default={}, nullable=False) # Strategic settings (Currency, Mutualization, etc.)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization {self.name} ({self.plan})>"

class User(Base):
    __tablename__ = "users"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=True) # Nullable pour Google OAuth
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Legacy Shop ID (Deprecated after migration)
    shop_id = Column(GUID, nullable=True, index=True)
    
    # Active context (for session persistence)
    current_organization_id = Column(GUID, nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    preferences = Column(JSON, default={}, nullable=False)
    
    # Relationships
    organizations = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

class OrganizationMember(Base):
    """
    OrganizationMember Model: Link table between User and Organization with role and permission management.
    """
    __tablename__ = "organization_members"

    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    permissions = Column(JSON, default={}, nullable=False) # Granular permissions

    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organizations")

class Invitation(Base):
    """
    Invitation Model: Manages pending collaborator access (US 16.5).
    """
    __tablename__ = "invitations"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    organization_id = Column(GUID, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    
    code = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    
    invited_by_id = Column(GUID, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="invitations")
