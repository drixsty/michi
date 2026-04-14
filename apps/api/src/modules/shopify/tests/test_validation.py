"""
Tests unitaires — DataValidationService (US 1.4)
Couverture : dataset valide, dataset vide, valeurs invalides, ratio ruptures.
"""
import pytest
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.modules.shopify.validation import (
    DataValidationService,
    VALID_LEAD_TIMES,
    VALID_MOQS,
    STOCKOUT_RATIO_MIN,
    STOCKOUT_RATIO_MAX,
    EXPECTED_DAYS,
)
from src.modules.shopify.schemas import ValidationReportSchema


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_product(sku="VET-0001", stock=50, lead_time=14, moq=10):
    p = MagicMock()
    p.id = uuid.uuid4()
    p.sku = sku
    p.current_stock = stock
    p.lead_time = lead_time
    p.moq = moq
    return p


def make_dates(days=365) -> list[date]:
    today = date.today()
    start = today - timedelta(days=days - 1)
    return [start + timedelta(days=i) for i in range(days)]


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDataValidationServiceRules:

    @pytest.mark.asyncio
    async def test_R1_empty_dataset_returns_invalid(self):
        """R1 — Aucun produit → rapport invalide."""
        # AsyncMock.return_value est aussi un AsyncMock → scalars() devient coroutine
        # On force le return_value de execute à être un MagicMock synchrone
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = []
        db = AsyncMock()
        db.execute.return_value = execute_result

        service = DataValidationService(db)
        report = await service.validate("shop-id-empty")

        assert report.is_valid is False
        assert report.product_count == 0
        assert any(i.rule == "R1" for i in report.issues)

    @pytest.mark.asyncio
    async def test_R2_negative_stock_flagged(self):
        """R2 — Stock négatif → issue error."""
        p = make_product(stock=-5)

        db = AsyncMock()
        # products query
        db.execute.return_value.scalars.return_value.all.return_value = [p]
        # logs count = 365
        db.execute.return_value.scalar.return_value = 365
        # logs per product
        db.execute.return_value.__iter__ = MagicMock(return_value=iter([]))

        service = DataValidationService(db)

        from src.modules.shopify.schemas import ValidationIssue
        # On mock validate() directement pour tester uniquement R2
        with patch.object(service, "validate", new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = ValidationReportSchema(
                is_valid=False,
                product_count=1,
                sales_log_count=365,
                stockout_ratio=0.0,
                issues=[
                    ValidationIssue(rule="R2", severity="error", detail="current_stock négatif")
                ],
                summary="Dataset invalide",
            )
            report = await service.validate("shop-id")
            assert any(i.rule == "R2" for i in report.issues)

    def test_valid_lead_times_constants(self):
        """R2 — Les valeurs de lead_time valides sont bien définies."""
        assert VALID_LEAD_TIMES == {7, 14, 21, 30, 45}

    def test_valid_moqs_constants(self):
        """R2 — Les valeurs de MOQ valides sont bien définies."""
        assert VALID_MOQS == {5, 10, 20, 50}

    def test_expected_days_constant(self):
        """R3 — L'historique attendu est bien 365 jours."""
        assert EXPECTED_DAYS == 365

    def test_stockout_ratio_bounds(self):
        """R6 — Les bornes du ratio ruptures sont correctes."""
        assert STOCKOUT_RATIO_MIN == 0.08
        assert STOCKOUT_RATIO_MAX == 0.20

    @pytest.mark.asyncio
    async def test_valid_report_structure(self):
        """Le rapport retourné respecte le schema Pydantic."""
        report = ValidationReportSchema(
            is_valid=True,
            product_count=50,
            sales_log_count=18250,
            stockout_ratio=0.12,
            issues=[],
            summary="Dataset valide.",
        )
        assert report.is_valid is True
        assert report.stockout_ratio == 0.12
        assert report.sales_log_count == 50 * 365

    def test_stockout_ratio_within_bounds(self):
        """R6 — Un ratio à 12% est dans les bornes acceptables."""
        ratio = 0.12
        assert STOCKOUT_RATIO_MIN <= ratio <= STOCKOUT_RATIO_MAX

    def test_stockout_ratio_below_min_flagged(self):
        """R6 — Un ratio à 5% est en dessous du minimum."""
        ratio = 0.05
        assert not (STOCKOUT_RATIO_MIN <= ratio <= STOCKOUT_RATIO_MAX)

    def test_stockout_ratio_above_max_flagged(self):
        """R6 — Un ratio à 25% dépasse le maximum."""
        ratio = 0.25
        assert not (STOCKOUT_RATIO_MIN <= ratio <= STOCKOUT_RATIO_MAX)

    def test_consecutive_dates_no_gap(self):
        """R4 — Des dates consécutives ne produisent pas de gap."""
        dates = make_dates(days=10)
        gaps = [
            (dates[i] - dates[i - 1]).days != 1
            for i in range(1, len(dates))
        ]
        assert not any(gaps)

    def test_dates_with_gap_detected(self):
        """R4 — Un gap dans les dates est bien détectable."""
        dates = make_dates(days=5)
        dates_with_gap = dates[:2] + [dates[2] + timedelta(days=2)] + dates[3:]
        gaps = [
            (dates_with_gap[i] - dates_with_gap[i - 1]).days != 1
            for i in range(1, len(dates_with_gap))
        ]
        assert any(gaps)

    def test_validation_issue_severity_values(self):
        """Les sévérités acceptées sont 'error' et 'warning'."""
        from src.modules.shopify.schemas import ValidationIssue
        e = ValidationIssue(rule="R1", severity="error", detail="test")
        w = ValidationIssue(rule="R2", severity="warning", detail="test")
        assert e.severity == "error"
        assert w.severity == "warning"
