from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class ChatSessionModel(Base):
    __tablename__ = "assistant_sessions"

    id = Column(String, primary_key=True) # session_id
    user_id = Column(String, nullable=False)
    org_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    title = Column(String, nullable=True)
    metadata_json = Column(JSON, default={})

    messages = relationship("ChatMessageModel", back_populates="session", cascade="all, delete-orphan")

class ChatMessageModel(Base):
    __tablename__ = "assistant_messages"

    id = Column(String, primary_key=True) # uuid
    session_id = Column(String, ForeignKey("assistant_sessions.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    rating = Column(String, nullable=True) # UP, DOWN
    feedback_text = Column(Text, nullable=True)

    session = relationship("ChatSessionModel", back_populates="messages")
