"""
Types GraphQL avec Strawberry
"""
import strawberry
from datetime import datetime
from uuid import UUID


@strawberry.type
class User:
    """Type User GraphQL"""
    id: strawberry.ID
    email: str
    shop_id: strawberry.ID
    created_at: datetime


@strawberry.input
class LoginInput:
    """Input pour mutation login"""
    email: str
    password: str


@strawberry.type
class AuthPayload:
    """Payload retourné par login"""
    token: str
    user: User
