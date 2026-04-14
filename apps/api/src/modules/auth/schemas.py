"""
Pydantic schemas pour Auth
"""
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class OrganizationSchema(BaseModel):
    id: UUID
    name: str
    slug: str
    plan: str
    subscription_status: str
    created_at: datetime
    updated_at: datetime
    settings: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrganizationMemberSchema(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: str
    permissions: dict
    organization: Optional[OrganizationSchema] = None
    
    model_config = ConfigDict(from_attributes=True)

class UserSchema(BaseModel):
    """Schema User pour GraphQL"""
    id: UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    current_organization_id: Optional[UUID] = None
    shop_id: Optional[UUID] = None
    preferences: Optional[dict] = None
    created_at: datetime
    
    # List of organizations the user belongs to
    organizations: List[OrganizationMemberSchema] = []
    
    model_config = ConfigDict(from_attributes=True)

class LoginInput(BaseModel):
    """Input pour mutation login"""
    email: EmailStr
    password: str

class AuthPayload(BaseModel):
    """Payload retourné par login"""
    token: str
    user: UserSchema
