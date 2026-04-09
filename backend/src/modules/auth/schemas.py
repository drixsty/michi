"""
Pydantic schemas pour Auth
"""
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class LoginInput(BaseModel):
    """Input pour mutation login"""
    email: EmailStr
    password: str


class UserSchema(BaseModel):
    """Schema User pour GraphQL"""
    id: UUID
    email: str
    shop_id: UUID
    created_at: datetime
    preferences: Optional[dict] = None
    
    class Config:
        from_attributes = True


class AuthPayload(BaseModel):
    """Payload retourné par login"""
    token: str
    user: UserSchema
