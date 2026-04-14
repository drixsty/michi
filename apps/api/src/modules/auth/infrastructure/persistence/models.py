import enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from src.core.database import Base

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
    Modèle Organization : Entité parente regroupant boutiques et utilisateurs.
    """
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Billing (Sprint 17/18)
    stripe_customer_id = Column(String(255), nullable=True)
    plan = Column(String(50), default="BASIC") # BASIC, PRO, ENTERPRISE
    subscription_status = Column(String(50), default="ACTIVE")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    settings = Column(JSONB, server_default='{}', default={}, nullable=False) # Paramètres stratégiques (Currency, Mutualisation, etc.)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    stores = relationship("Store", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization {self.name} ({self.plan})>"

class OrganizationMember(Base):
    """
    Table de liaison User <-> Organization avec gestion des rôles et droits.
    """
    __tablename__ = "organization_members"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    permissions = Column(JSONB, default={}, nullable=False) # Droits granulaires

    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="organizations")

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=True) # Nullable pour Google OAuth
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    
    # Legacy Shop ID (Deprecated after migration)
    shop_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Active context (for session persistence)
    current_organization_id = Column(UUID(as_uuid=True), nullable=True)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    preferences = Column(JSONB, default={}, nullable=False)
    
    # Relationships
    organizations = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

class Invitation(Base):
    """
    Modèle Invitation : Gère les accès collaborateurs en attente (US 16.5).
    """
    __tablename__ = "invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    
    code = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    
    invited_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="invitations")
