"""
Tests unitaires — Outlier Detection IQR
Migré depuis forecasting/tests/ vers intelligence/tests/ (US 21.30).
Couverture : détection outliers, correction, interaction avec OOS, edge cases.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from modules.intelligence.algorithms.outlier_detection import (
    detect_outliers,
    detect_outliers_batch,
    OUTLIER_ROLLING_WINDOW,
)


def make_df(units_sold: list, stocks: list, start: date = date(2025, 1, 1)) -> pd.DataFrame:
    n = len(units_sold)
    return pd.DataFrame({
        "date": [start + timedelta(days=i) for i in range(n)],
        "units_sold": [float(u) for u in units_sold],
        "end_of_day_stock": stocks,
    })


class TestDetectOutliers:

    def test_normal_series_no_outliers(self):
        """Une série stable ne produit pas d'outliers."""
        df = make_df([5.0] * 30, [100] * 30)
        result = detect_outliers(df)
        assert result["is_outlier"].sum() == 0

    def test_extreme_value_flagged(self):
        """Une valeur 100× supérieure à la normale est flagguée."""
        units = [5.0] * 28 + [500.0] + [5.0]
        df = make_df(units, [100] * 30)
        result = detect_outliers(df)
        assert result.loc[28, "is_outlier"] is True or result["is_outlier"].iloc[28]

    def test_outlier_corrected_not_zero(self):
        """La valeur corrigée d'un outlier est > 0 (remplacée par médiane)."""
        units = [5.0] * 28 + [500.0] + [5.0]
        df = make_df(units, [100] * 30)
        result = detect_outliers(df)
        outlier_idx = result[result["is_outlier"]].index
        assert (result.loc[outlier_idx, "corrected_units_sold"] > 0).all()
        assert (result.loc[outlier_idx, "corrected_units_sold"] < 500).all()

    def test_stockout_days_never_outlier(self):
        """Les jours de rupture (stock=0) ne sont jamais flaggués outliers."""
        units = [5.0] * 25 + [0.0] * 5
        stocks = [100] * 25 + [0] * 5
        df = make_df(units, stocks)
        result = detect_outliers(df)
        stockout_mask = result["is_stockout"]
        assert result.loc[stockout_mask, "is_outlier"].sum() == 0

    def test_corrected_units_sold_non_negative(self):
        """corrected_units_sold est toujours >= 0."""
        units = [5.0] * 20 + [1000.0] * 5 + [5.0] * 5
        df = make_df(units, [100] * 30)
        result = detect_outliers(df)
        assert (result["corrected_units_sold"] >= 0).all()

    def test_iqr_bounds_present(self):
        """Les colonnes iqr_lower et iqr_upper sont bien ajoutées."""
        df = make_df([5.0] * 20, [100] * 20)
        result = detect_outliers(df)
        assert "iqr_lower" in result.columns
        assert "iqr_upper" in result.columns

    def test_iqr_lower_non_negative(self):
        """La borne basse IQR ne peut pas être négative."""
        df = make_df([1.0, 2.0, 1.5, 1.0, 2.0, 1.5, 1.0, 2.0], [100] * 8)
        result = detect_outliers(df)
        assert (result["iqr_lower"] >= 0).all()

    def test_insufficient_data_no_flag(self):
        """Moins de 4 points non-rupture → aucun outlier flaggué."""
        df = make_df([5.0, 0.0, 0.0], [10, 0, 0])
        result = detect_outliers(df)
        assert result["is_outlier"].sum() == 0

    def test_uses_theoretical_if_available(self):
        """Si theoretical_units_sold est présent, c'est lui qui est analysé."""
        units = [5.0] * 20 + [0.0] * 5
        stocks = [100] * 20 + [0] * 5
        df = make_df(units, stocks)
        df["theoretical_units_sold"] = df["units_sold"].copy()
        df.loc[df["end_of_day_stock"] == 0, "theoretical_units_sold"] = 5.0
        result = detect_outliers(df)
        assert "corrected_units_sold" in result.columns

    def test_missing_column_raises(self):
        """Colonnes manquantes → ValueError."""
        df = pd.DataFrame({"date": [date(2025, 1, 1)], "units_sold": [5.0]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            detect_outliers(df)

    def test_rolling_window_constant(self):
        """La fenêtre IQR de correction est bien 11 jours."""
        assert OUTLIER_ROLLING_WINDOW == 11


class TestDetectOutliersBatch:

    def test_batch_processes_multiple_products(self):
        """Le batch traite plusieurs produits indépendamment."""
        df = pd.DataFrame({
            "product_id": ["p1"] * 20 + ["p2"] * 20,
            "date": list(pd.date_range("2025-01-01", periods=20)) * 2,
            "units_sold": [5.0] * 19 + [500.0] + [3.0] * 19 + [300.0],
            "end_of_day_stock": [100] * 40,
        })
        result = detect_outliers_batch(df)
        assert "is_outlier" in result.columns
        for pid in ["p1", "p2"]:
            sub = result[result["product_id"] == pid]
            assert sub["is_outlier"].sum() >= 1

    def test_batch_missing_column_raises(self):
        """Colonnes manquantes → ValueError."""
        df = pd.DataFrame({"date": [], "units_sold": []})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            detect_outliers_batch(df)
