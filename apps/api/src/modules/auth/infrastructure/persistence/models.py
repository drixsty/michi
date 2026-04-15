from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base, GUID
from core.database.constants import UserRole, InvitationStatus
from core.database.models import Organization, User, OrganizationMember

class Invitation(Base):
    """
    Invitation Model: Manages pending collaborator access.
    Kept in Auth module as it's part of the authentication/onboarding logic.
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
