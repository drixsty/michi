"""
Tests unitaires — intelligence/analytics/risk_scoring.py
"""
import pytest
from datetime import date
from typing import Any
from modules.intelligence.analytics.risk_scoring import RiskItem, score_products


def _make_sku(
    stock: int = 100,
    run_rate: float = 5.0,
    risk_value: float = 200.0,
    reorder_quantity: int = 10,
    title: str = "Produit Test",
    platforms: set[str] | None = None,
    cost: float = 10.0,
    sale: float = 20.0,
    supplier_id: str | None = None,
    product_id: str = "abc123",
) -> dict[str, Any]:
    return {
        "product_id": product_id,
        "stock": stock,
        "run_rate": run_rate,
        "risk_value": risk_value,
        "reorder_quantity": reorder_quantity,
        "title": title,
        "platforms": platforms or {"SHOPIFY"},
        "cost": cost,
        "sale": sale,
        "supplier_id": supplier_id,
    }


class TestScoreProducts:
    def test_basic_coverage_calculation(self) -> None:
        agg = {"SKU001": _make_sku(stock=50, run_rate=5.0)}
        items, avg_cov = score_products(agg)
        assert len(items) == 1
        assert items[0].days_of_stock == 10.0
        assert avg_cov == 10.0

    def test_zero_runrate_gives_none_days(self) -> None:
        agg = {"SKU001": _make_sku(stock=100, run_rate=0.0)}
        items, avg_cov = score_products(agg)
        assert items[0].days_of_stock is None
        assert items[0].stockout_date is None
        assert avg_cov == 0.0

    def test_sorted_by_risk_value_descending(self) -> None:
        agg = {
            "SKU001": _make_sku(risk_value=100.0),
            "SKU002": _make_sku(risk_value=500.0),
            "SKU003": _make_sku(risk_value=250.0),
        }
        items, _ = score_products(agg)
        assert items[0].risk_value == 500.0
        assert items[1].risk_value == 250.0
        assert items[2].risk_value == 100.0

    def test_stockout_date_is_future_or_today(self) -> None:
        agg = {"SKU001": _make_sku(stock=10, run_rate=5.0)}
        items, _ = score_products(agg)
        item = items[0]
        assert item.stockout_date is not None
        assert item.stockout_date >= date.today()

    def test_empty_aggregation(self) -> None:
        items, avg_cov = score_products({})
        assert items == []
        assert avg_cov == 0.0

    def test_platforms_joined(self) -> None:
        agg = {"SKU001": _make_sku(platforms={"SHOPIFY", "WOO"})}
        items, _ = score_products(agg)
        assert "SHOPIFY" in items[0].source_platform
        assert "WOO" in items[0].source_platform

    def test_avg_coverage_excludes_zero_runrate(self) -> None:
        agg = {
            "SKU001": _make_sku(stock=20, run_rate=2.0),
            "SKU002": _make_sku(stock=100, run_rate=0.0),
        }
        items, avg_cov = score_products(agg)
        assert avg_cov == 10.0

    def test_returns_risk_item_dataclass(self) -> None:
        agg = {"SKU001": _make_sku()}
        items, _ = score_products(agg)
        assert isinstance(items[0], RiskItem)
        with pytest.raises(Exception):
            items[0].risk_value = 999.0  # type: ignore[misc]
