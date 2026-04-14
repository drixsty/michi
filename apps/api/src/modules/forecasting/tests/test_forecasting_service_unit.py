"""
Tests ForecastingService — Sprint 21 (US 21.24).

Tests unitaires via faux repositories in-memory.
Aucune dépendance PostgreSQL/SQLAlchemy.
"""
from __future__ import annotations

import uuid
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from uuid import UUID

import pytest

from src.modules.forecasting.application.forecasting_service import ForecastingService
from src.modules.forecasting.domain.entities import CleanedDemandEntity, PredictionEntity
from src.modules.forecasting.domain.ports import ICleanedDemandRepository, IPredictionRepository
from src.modules.inventory.domain.entities import ProductEntity, SalesLogEntity, StoreEntity, PlatformSource
from src.modules.inventory.domain.ports import IProductRepository, ISalesLogRepository, IStoreRepository


# ---------------------------------------------------------------------------
# Fake Repositories
# ---------------------------------------------------------------------------

class FakeCleanedDemandRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, CleanedDemandEntity] = {}

    async def list_by_product(self, product_id: UUID, limit: int = 365) -> List[CleanedDemandEntity]:
        return [d for d in self._store.values() if d.product_id == product_id][:limit]

    async def save_batch(self, entities: List[CleanedDemandEntity]) -> None:
        for e in entities:
            self._store[e.id] = e

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        self._store = {k: v for k, v in self._store.items() if v.product_id not in product_ids}


class FakePredictionRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, PredictionEntity] = {}

    async def get_by_product(self, product_id: UUID) -> Optional[PredictionEntity]:
        for p in self._store.values():
            if p.product_id == product_id:
                return p
        return None

    async def list_by_store(self, store_id: UUID) -> List[PredictionEntity]:
        return list(self._store.values())

    async def list_by_organization(self, org_id: UUID) -> List[PredictionEntity]:
        return list(self._store.values())

    async def save(self, prediction: PredictionEntity) -> PredictionEntity:
        self._store[prediction.id] = prediction
        return prediction

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        self._store = {k: v for k, v in self._store.items() if v.product_id not in product_ids}


class FakeProductRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, ProductEntity] = {}

    async def list_by_store(self, store_ids: List[UUID]) -> List[ProductEntity]:
        return [p for p in self._store.values() if p.store_id in store_ids]

    async def get_by_id(self, product_id: UUID) -> Optional[ProductEntity]:
        return self._store.get(product_id)

    async def save(self, product: ProductEntity) -> ProductEntity:
        self._store[product.id] = product
        return product

    def seed(self, product: ProductEntity) -> None:
        self._store[product.id] = product


class FakeSalesLogRepository:
    def __init__(self) -> None:
        self._store: list = []

    async def list_by_product(self, product_id: UUID, limit: int = 365) -> List[SalesLogEntity]:
        return [s for s in self._store if s.product_id == product_id]

    def seed_logs(self, logs: List[SalesLogEntity]) -> None:
        self._store.extend(logs)

    async def save_batch(self, logs: List[SalesLogEntity]) -> None:
        self._store.extend(logs)

    async def delete_by_products(self, product_ids: List[UUID]) -> None:
        self._store = [s for s in self._store if s.product_id not in product_ids]


class FakeStoreRepository:
    def __init__(self) -> None:
        self._store: Dict[UUID, StoreEntity] = {}

    async def get_by_id(self, store_id: UUID) -> Optional[StoreEntity]:
        return self._store.get(store_id)

    def seed(self, store: StoreEntity) -> None:
        self._store[store.id] = store


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_forecasting_service(
    cleaned_demand_repo=None, prediction_repo=None,
    product_repo=None, sales_log_repo=None, store_repo=None
):
    return ForecastingService(
        cleaned_demand_repo=cleaned_demand_repo or FakeCleanedDemandRepository(),
        prediction_repo=prediction_repo or FakePredictionRepository(),
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
        cost_price=10.0,
        sale_price=25.0,
    )


def _make_sales_logs(product_id: UUID, days: int = 30, daily_sales: float = 5.0) -> List[SalesLogEntity]:
    logs = []
    for i in range(days):
        d = date.today() - timedelta(days=days - i)
        logs.append(SalesLogEntity(
            id=uuid.uuid4(),
            product_id=product_id,
            date=d,
            units_sold=daily_sales,
            end_of_day_stock=max(0, 50 - int(daily_sales * i)),
        ))
    return logs


# ---------------------------------------------------------------------------
# get_predictions()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_predictions_by_org_returns_list() -> None:
    prediction_repo = FakePredictionRepository()
    prediction = PredictionEntity(
        id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        run_rate=5.0,
        days_of_stock=10.0,
        predicted_stockout_date=date.today() + timedelta(days=10),
        reorder_quantity=50,
        current_stock_snapshot=50.0,
        lead_time_snapshot=7,
        moq_snapshot=10,
        computed_at=datetime.utcnow(),
    )
    await prediction_repo.save(prediction)
    service = _make_forecasting_service(prediction_repo=prediction_repo)

    results = await service.get_predictions(org_id=str(uuid.uuid4()))
    assert len(results) == 1
    assert results[0].run_rate == 5.0


@pytest.mark.asyncio
async def test_get_predictions_no_context_returns_empty() -> None:
    service = _make_forecasting_service()
    results = await service.get_predictions()
    assert results == []


# ---------------------------------------------------------------------------
# run_cleaning_pipeline()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_cleaning_pipeline_no_products_returns_failure() -> None:
    store_id = str(uuid.uuid4())
    service = _make_forecasting_service()

    result = await service.run_cleaning_pipeline(store_id)
    assert result.success is False
    assert result.products_processed == 0


@pytest.mark.asyncio
async def test_run_cleaning_pipeline_no_logs_returns_failure() -> None:
    product_repo = FakeProductRepository()
    sales_log_repo = FakeSalesLogRepository()
    store_id = uuid.uuid4()

    product = _make_product(store_id)
    product_repo.seed(product)

    service = _make_forecasting_service(
        product_repo=product_repo,
        sales_log_repo=sales_log_repo
    )

    result = await service.run_cleaning_pipeline(str(store_id))
    assert result.success is False
    assert "historique" in result.message.lower()


@pytest.mark.asyncio
async def test_run_cleaning_pipeline_success() -> None:
    product_repo = FakeProductRepository()
    sales_log_repo = FakeSalesLogRepository()
    cleaned_demand_repo = FakeCleanedDemandRepository()
    store_id = uuid.uuid4()

    product = _make_product(store_id)
    product_repo.seed(product)
    sales_log_repo.seed_logs(_make_sales_logs(product.id, days=30))

    service = _make_forecasting_service(
        product_repo=product_repo,
        sales_log_repo=sales_log_repo,
        cleaned_demand_repo=cleaned_demand_repo,
    )

    result = await service.run_cleaning_pipeline(str(store_id))
    assert result.success is True
    assert result.products_processed >= 1
    assert result.rows_written >= 1


# ---------------------------------------------------------------------------
# run_prediction_pipeline()
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_prediction_pipeline_no_products_returns_failure() -> None:
    service = _make_forecasting_service()
    result = await service.run_prediction_pipeline(str(uuid.uuid4()))
    assert result.success is False


@pytest.mark.asyncio
async def test_run_prediction_pipeline_full_success() -> None:
    product_repo = FakeProductRepository()
    sales_log_repo = FakeSalesLogRepository()
    cleaned_demand_repo = FakeCleanedDemandRepository()
    prediction_repo = FakePredictionRepository()
    store_id = uuid.uuid4()

    product = _make_product(store_id)
    product_repo.seed(product)
    logs = _make_sales_logs(product.id, days=35)
    sales_log_repo.seed_logs(logs)

    service = _make_forecasting_service(
        product_repo=product_repo,
        sales_log_repo=sales_log_repo,
        cleaned_demand_repo=cleaned_demand_repo,
        prediction_repo=prediction_repo,
    )

    # D'abord nettoyage
    await service.run_cleaning_pipeline(str(store_id))
    
    # Puis prédiction
    result = await service.run_prediction_pipeline(str(store_id))
    assert result.success is True
    assert result.products_processed >= 1
