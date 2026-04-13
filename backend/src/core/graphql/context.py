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
    - user_id: ID de l'utilisateur connecté
    - org_id: ID de l'organisation active (contexte de session)
    """
    db: Optional[AsyncSession] = None # Sérialisé via SerializedAsyncSession pour éviter les conflits GraphQL
    user_id: Optional[str] = None
    org_id: Optional[str] = None
