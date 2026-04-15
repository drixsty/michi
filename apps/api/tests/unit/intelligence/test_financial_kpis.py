"""
Tests unitaires — intelligence/analytics/financial_kpis.py
"""
import pytest
from typing import Any
from src.modules.intelligence.analytics.financial_kpis import (
    FinancialKpis,
    calculate_financial_kpis,
)


class TestFinancialKpis:
    def test_basic_single_sku(self) -> None:
        agg: dict[str, dict[str, Any]] = {
            "SKU001": {
                "stock": 100, "cost": 10.0, "sale": 20.0,
                "run_rate": 5.0, "risk_value": 200.0, "coverage_days": 20.0,
            }
        }
        kpis = calculate_financial_kpis(agg)
        assert kpis.inventory_value_cost == 1000.0
        assert kpis.inventory_value_sale == 2000.0
        assert kpis.revenue_at_risk == 200.0
        assert kpis.stock_coverage_avg_days == 20.0
        assert kpis.total_run_rate == 5.0
        assert kpis.total_stock == 100
        assert kpis.avg_sale_price == 20.0

    def test_empty_aggregation(self) -> None:
        kpis = calculate_financial_kpis({})
        assert kpis.inventory_value_cost == 0.0
        assert kpis.inventory_value_sale == 0.0
        assert kpis.revenue_at_risk == 0.0
        assert kpis.stock_coverage_avg_days == 0.0
        assert kpis.total_stock == 0
        assert kpis.avg_sale_price == 0.0

    def test_multiple_skus(self) -> None:
        agg: dict[str, dict[str, Any]] = {
            "SKU001": {
                "stock": 100, "cost": 10.0, "sale": 20.0,
                "run_rate": 5.0, "risk_value": 100.0, "coverage_days": 20.0,
            },
            "SKU002": {
                "stock": 50, "cost": 5.0, "sale": 15.0,
                "run_rate": 2.0, "risk_value": 75.0, "coverage_days": 25.0,
            },
        }
        kpis = calculate_financial_kpis(agg)
        assert kpis.inventory_value_cost == 1250.0
        assert kpis.inventory_value_sale == 2750.0
        assert kpis.revenue_at_risk == 175.0
        assert kpis.stock_coverage_avg_days == 22.5
        assert kpis.total_run_rate == 7.0
        assert kpis.total_stock == 150

    def test_sku_without_runrate_excluded_from_avg(self) -> None:
        agg: dict[str, dict[str, Any]] = {
            "SKU001": {
                "stock": 100, "cost": 10.0, "sale": 20.0,
                "run_rate": 5.0, "risk_value": 0.0, "coverage_days": 20.0,
            },
            "SKU002": {
                "stock": 50, "cost": 5.0, "sale": 15.0,
                "run_rate": 0.0, "risk_value": 0.0, "coverage_days": None,
            },
        }
        kpis = calculate_financial_kpis(agg)
        assert kpis.stock_coverage_avg_days == 20.0

    def test_returns_frozen_dataclass(self) -> None:
        kpis = calculate_financial_kpis({})
        assert isinstance(kpis, FinancialKpis)
        with pytest.raises(Exception):
            kpis.total_stock = 999  # type: ignore[misc]
