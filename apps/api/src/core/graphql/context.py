"""
GraphQL Context
Injecté dans chaque resolver via info.context

Sprint 21 — US 21.12 : DI Container complet.
Tous les services applicatifs sont pré-construits et accessibles via info.context.services.
Les helpers directs (auth_service, org_service...) facilitent la migration progressive.
"""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional


from strawberry.fastapi import BaseContext
from src.core.di import ServiceContainer

@dataclass
class GraphQLContext(BaseContext):
    """
    Context GraphQL injecté dans chaque resolver.
    
    Contient:
    - db: Session SQLAlchemy async
    - user_id: ID de l'utilisateur connecté
    - org_id: ID de l'organisation active (contexte de session)
    - services: Conteneur de tous les services applicatifs (DI Sprint 21)
    - billing: BillingService (accès direct pour le module billing)
    """
    db: Optional[AsyncSession] = None 
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    
    # Services (Sprint 17 & 21)
    billing: Optional[object] = None  # BillingService
    services: Optional[ServiceContainer] = None

    # ---------- Helpers directs (US 21.12) ----------

    @property
    def auth_service(self):
        """Accès direct à auth_service (raccourci pour les resolvers Auth)."""
        return self.services.auth_service if self.services else None

    @property
    def org_service(self):
        """Accès direct à org_service (raccourci pour les resolvers Org)."""
        return self.services.org_service if self.services else None

    @property
    def inventory_service(self):
        """Accès direct à inventory_service (raccourci pour les resolvers Inventory)."""
        return self.services.inventory_service if self.services else None

    @property
    def forecasting_service(self):
        """Accès direct à forecasting_service (raccourci pour les resolvers Forecasting)."""
        return self.services.forecasting_service if self.services else None

    @property
    def alert_service(self):
        """Accès direct à alert_service."""
        return self.services.alert_service if self.services else None
