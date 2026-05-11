"""
Tests InventoryService — Sprint 21 (US 21.24).

Tests unitaires avec faux repositories in-memory.
Aucun accès PostgreSQL requis.
"""

import uuid
from datetime import datetime, date
from typing import Dict, List, Optional
from uuid import UUID

import pytest

from modules.inventory.application.inventory_service import InventoryService
from modules.inventory.domain.entities import (
    AlertEntity, PlatformSource, ProductEntity, SalesLogEntity, StoreEntity
)
from modules.inventory.domain.ports import (
    IAlertRepository, IProductRepository, ISalesLogRepository, IStoreRepository
)


# ---------------------------------------------------------------------------
# Fake Repositories (in-memory)
# ---------------------------------------------------------------------------

class FakeProductRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, ProductEntity] = {}

    async def get_by_id(self, product_id: UUID) -> Optional[ProductEntity]:
        return self._store.get(product_id)

    async def list_by_store(self, store_ids: List[UUID]) -> List[ProductEntity]:
        return [p for p in self._store.values() if p.store_id in store_ids]

    async def get_by_sku(self, sku: str, store_ids: List[UUID]) -> List[ProductEntity]:
        return [p for p in self._store.values() if p.sku == sku and p.store_id in store_ids]

    async def save(self, product: ProductEntity) -> ProductEntity:
        self._store[product.id] = product
        return product

    async def update_settings(self, product_id: UUID, **kwargs) -> Optional[ProductEntity]:
        product = self._store.get(product_id)
        if not product:
            return None
        for k, v in kwargs.items():
            if hasattr(product, k):
                setattr(product, k, v)
        return product

    async def delete_by_store(self, store_id: UUID) -> None:
        self._store = {k: v for k, v in self._store.items() if v.store_id != store_id}


class FakeSalesLogRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, SalesLogEntity] = {}

    async def list_by_product(self, product_id: UUID, limit: int = 365) -> List[SalesLogEntity]:
        return [s for s in self._store.values() if s.product_id == product_id]

    async def save_batch(self, logs: List[SalesLogEntity]) -> None:
        for log in logs:
            self._store[log.id] = log

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        self._store = {k: v for k, v in self._store.items() if v.product_id not in product_ids}


class FakeStoreRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, StoreEntity] = {}

    async def get_by_id(self, store_id: UUID) -> Optional[StoreEntity]:
        return self._store.get(store_id)

    async def get_by_platform(self, org_id: UUID, platform: str) -> Optional[StoreEntity]:
        for s in self._store.values():
            if s.organization_id == org_id and s.platform.value == platform.upper():
                return s
        return None

    async def list_by_organization(self, org_id: UUID) -> List[StoreEntity]:
        return [s for s in self._store.values() if s.organization_id == org_id]

    async def save(self, store: StoreEntity) -> StoreEntity:
        self._store[store.id] = store
        return store

    def seed_store(self, store: StoreEntity) -> None:
        self._store[store.id] = store


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_inventory_service(product_repo=None, sales_log_repo=None, store_repo=None):
    return InventoryService(
        product_repo=product_repo or FakeProductRepository(),
        sales_log_repo=sales_log_repo or FakeSalesLogRepository(),
        store_repo=store_repo or FakeStoreRepository(),
    )


def _make_product(store_id: UUID, sku: str = "SKU-001", stock: int = 50) -> ProductEntity:
    return ProductEntity(
        id=uuid.uuid4(),
        store_id=store_id,
        sku=sku,
        title=f"Produit {sku}",
        current_stock=stock,
        lead_time=7,
        moq=10,
    )


# ---------------------------------------------------------------------------
# get_products()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_products_by_store() -> None:
    product_repo = FakeProductRepository()
    store_id = uuid.uuid4()
    product = _make_product(store_id)
    await product_repo.save(product)

    service = _make_inventory_service(product_repo=product_repo)
    results = await service.get_products([str(store_id)])

    assert len(results) == 1
    assert results[0].sku == product.sku


@pytest.mark.asyncio
async def test_get_products_by_id() -> None:
    product_repo = FakeProductRepository()
    store_id = uuid.uuid4()
    product = _make_product(store_id)
    await product_repo.save(product)

    service = _make_inventory_service(product_repo=product_repo)
    results = await service.get_products([str(store_id)], product_id=str(product.id))

    assert len(results) == 1
    assert results[0].id == product.id


@pytest.mark.asyncio
async def test_get_products_empty_store_returns_empty() -> None:
    service = _make_inventory_service()
    results = await service.get_products([str(uuid.uuid4())])
    assert results == []


# ---------------------------------------------------------------------------
# update_product_settings()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_product_settings_lead_time() -> None:
    product_repo = FakeProductRepository()
    store_id = uuid.uuid4()
    product = _make_product(store_id)
    await product_repo.save(product)

    service = _make_inventory_service(product_repo=product_repo)
    updated = await service.update_product_settings(str(product.id), lead_time=21)

    assert updated is not None
    assert updated.lead_time == 21


@pytest.mark.asyncio
async def test_update_product_settings_unknown_id_raises() -> None:
    service = _make_inventory_service()
    with pytest.raises(Exception):
        await service.update_product_settings(str(uuid.uuid4()), lead_time=5)


# ---------------------------------------------------------------------------
# toggle_source()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_toggle_source_creates_new_store() -> None:
    store_repo = FakeStoreRepository()
    product_repo = FakeProductRepository()
    org_id = uuid.uuid4()

    service = _make_inventory_service(product_repo=product_repo, store_repo=store_repo)
    store = await service.toggle_source(
        org_id=org_id,
        platform="SHOPIFY",
        connected=True,
    )

    assert store is not None
    assert store.connected is True
    assert store.platform == PlatformSource.SHOPIFY


@pytest.mark.asyncio
async def test_toggle_source_disconnect_deletes_products() -> None:
    store_repo = FakeStoreRepository()
    product_repo = FakeProductRepository()
    org_id = uuid.uuid4()
    
    service = _make_inventory_service(product_repo=product_repo, store_repo=store_repo)
    
    # D'abord connecter
    store = await service.toggle_source(org_id=org_id, platform="CSV", connected=True)
    
    # Ajouter un produit
    product = _make_product(store.id)
    await product_repo.save(product)
    assert len(await product_repo.list_by_store([store.id])) == 1
    
    # Déconnecter — les produits doivent être supprimés
    await service.toggle_source(
        org_id=org_id,
        platform="CSV",
        connected=False,
        store_id=store.id
    )
    
    remaining = await product_repo.list_by_store([store.id])
    assert len(remaining) == 0


# ---------------------------------------------------------------------------
# upsert_inventory_data()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upsert_creates_new_products() -> None:
    product_repo = FakeProductRepository()
    sales_log_repo = FakeSalesLogRepository()
    service = _make_inventory_service(product_repo=product_repo, sales_log_repo=sales_log_repo)

    store_id = str(uuid.uuid4())
    products_data = [
        {"sku": "ABC-001", "title": "T-Shirt Rouge", "current_stock": 100},
        {"sku": "ABC-002", "title": "Jean Bleu", "current_stock": 30},
    ]
    sales_data: list = []

    result = await service.upsert_inventory_data(
        shop_id=store_id,
        platform=PlatformSource.SHOPIFY,
        products_data=products_data,
        sales_data=sales_data,
    )

    assert result["products_count"] == 2
    all_products = await product_repo.list_by_store([UUID(store_id)])
    assert len(all_products) == 2


@pytest.mark.asyncio
async def test_upsert_updates_existing_products() -> None:
    product_repo = FakeProductRepository()
    service = _make_inventory_service(product_repo=product_repo)

    store_id = str(uuid.uuid4())
    products_data = [{"sku": "ABC-001", "title": "T-Shirt Original", "current_stock": 50}]
    await service.upsert_inventory_data(
        shop_id=store_id,
        platform=PlatformSource.SHOPIFY,
        products_data=products_data,
        sales_data=[],
    )

    # Update
    updated_data = [{"sku": "ABC-001", "title": "T-Shirt Updated", "current_stock": 75}]
    await service.upsert_inventory_data(
        shop_id=store_id,
        platform=PlatformSource.SHOPIFY,
        products_data=updated_data,
        sales_data=[],
    )

    all_products = await product_repo.list_by_store([UUID(store_id)])
    assert len(all_products) == 1
    assert all_products[0].title == "T-Shirt Updated"
    assert all_products[0].current_stock == 75
