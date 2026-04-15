from core.database.models import Organization, User, OrganizationMember
"""
Domain Ports for Forecasting Module
Abstract interfaces for repositories.
"""
from typing import List, Optional, Protocol
from uuid import UUID
from .entities import CleanedDemandEntity, PredictionEntity

class ICleanedDemandRepository(Protocol):
    async def list_by_product(self, product_id: UUID, limit: int = 365) -> List[CleanedDemandEntity]:
        """Fetch cleaned demand history for a product."""
        ...

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        """Clear cleaned demand for products."""
        ...

    async def save_batch(self, entities: List[CleanedDemandEntity]) -> None:
        """Batch insert cleaned demand entries."""
        ...

class IPredictionRepository(Protocol):
    async def get_by_product(self, product_id: UUID) -> Optional[PredictionEntity]:
        """Fetch current prediction for a single product."""
        ...

    async def save(self, entity: PredictionEntity) -> PredictionEntity:
        """Save or update a prediction."""
        ...

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        """Delete predictions for specific products."""
        ...

    async def list_by_store(self, store_id: UUID) -> List[PredictionEntity]:
        """List current predictions for all products in a store."""
        ...

    async def list_by_organization(self, org_id: UUID) -> List[PredictionEntity]:
        """List current predictions for all products in an organization."""
        ...
