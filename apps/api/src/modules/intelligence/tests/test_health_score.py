"""
Tests unitaires — intelligence/analytics/health_score.py
"""
import pytest
from src.modules.intelligence.analytics.health_score import calculate_health_score


class TestHealthScore:
    def test_perfect_score(self) -> None:
        score = calculate_health_score(
            revenue_at_risk=0,
            total_run_rate=10,
            avg_sale_price=50,
            avg_coverage_days=30,
            stockout_count=0,
            total_skus=100,
        )
        assert score == 100

    def test_score_range_0_to_100(self) -> None:
        for _ in range(10):
            score = calculate_health_score(
                revenue_at_risk=999999,
                total_run_rate=1,
                avg_sale_price=1,
                avg_coverage_days=0,
                stockout_count=100,
                total_skus=100,
            )
            assert 0 <= score <= 100

    def test_critical_coverage_degrades_score(self) -> None:
        score_critical = calculate_health_score(0, 10, 50, 3, 0, 100)
        score_optimal = calculate_health_score(0, 10, 50, 30, 0, 100)
        assert score_critical < score_optimal

    def test_overstock_degrades_score(self) -> None:
        score_overstock = calculate_health_score(0, 10, 50, 120, 0, 100)
        score_optimal = calculate_health_score(0, 10, 50, 30, 0, 100)
        assert score_overstock < score_optimal

    def test_stockouts_degrade_score(self) -> None:
        score_no_stockout = calculate_health_score(0, 10, 50, 30, 0, 100)
        score_with_stockout = calculate_health_score(0, 10, 50, 30, 20, 100)
        assert score_with_stockout < score_no_stockout

    def test_zero_skus_returns_valid(self) -> None:
        score = calculate_health_score(0, 0, 0, 0, 0, 0)
        assert 0 <= score <= 100

    def test_rotation_boundary_7_days(self) -> None:
        score_7 = calculate_health_score(0, 10, 50, 7, 0, 100)
        score_6 = calculate_health_score(0, 10, 50, 6, 0, 100)
        assert score_7 >= score_6

    def test_rotation_boundary_45_days(self) -> None:
        score_45 = calculate_health_score(0, 10, 50, 45, 0, 100)
        score_46 = calculate_health_score(0, 10, 50, 46, 0, 100)
        assert score_45 >= score_46
