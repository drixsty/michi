"""
User SQLAlchemy Model
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from src.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    shop_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Notification & User preferences (US 11.2)
    from sqlalchemy.dialects.postgresql import JSONB
    preferences = Column(JSONB, default={}, nullable=False)
    
    def __repr__(self):
        return f"<User {self.email}>"
