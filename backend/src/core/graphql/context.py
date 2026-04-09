"""
GraphQL Context
Injecté dans chaque resolver via info.context
"""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional


from strawberry.fastapi import BaseContext


@dataclass
class GraphQLContext(BaseContext):
    """
    Context GraphQL injecté dans chaque resolver.
    
    Contient:
    - db: Session SQLAlchemy async
    - user_id: ID de l'utilisateur connecté (None si non authentifié)
    - shop_id: ID du shop de l'utilisateur (None si non authentifié)
    """
    db: Optional[AsyncSession] = None
    user_id: Optional[str] = None
    shop_id: Optional[str] = None
