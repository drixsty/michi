"""
Tests unitaires — Run Rate Algorithm
Migré depuis forecasting/tests/ vers intelligence/tests/ (US 21.30).
Couverture : calcul run rate, fenêtre glissante, fallback, edge cases, batch.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from modules.intelligence.algorithms.run_rate import (
    calculate_run_rate,
    calculate_run_rate_batch,
    RUN_RATE_WINDOW,
    RUN_RATE_MIN_PERIODS,
)


def make_df(
    corrected: list,
    start: date = date(2025, 1, 1),
    is_stockout: list | None = None,
    is_outlier: list | None = None,
) -> pd.DataFrame:
    n = len(corrected)
    df = pd.DataFrame({
        "date": [start + timedelta(days=i) for i in range(n)],
        "corrected_units_sold": [float(v) for v in corrected],
    })
    if is_stockout is not None:
        df["is_stockout"] = is_stockout
    if is_outlier is not None:
        df["is_outlier"] = is_outlier
    return df


class TestCalculateRunRate:

    def test_constant_series_run_rate(self):
        """Série constante de 35j → run_rate == valeur constante."""
        df = make_df([10.0] * 35)
        result = calculate_run_rate(df)
        assert abs(float(result["run_rate"].iloc[-1]) - 10.0) < 0.01

    def test_run_rate_non_negative(self):
        """Le run rate ne doit jamais être négatif."""
        df = make_df([0.0] * 40)
        result = calculate_run_rate(df)
        assert (result["run_rate"] >= 0).all()

    def test_run_rate_column_created(self):
        """La colonne run_rate est bien ajoutée au DataFrame."""
        df = make_df([5.0] * 10)
        result = calculate_run_rate(df)
        assert "run_rate" in result.columns

    def test_short_series_fallback_global_median(self):
        """Série < min_periods jours → fallback sur médiane globale."""
        df = make_df([8.0, 8.0, 8.0])
        result = calculate_run_rate(df)
        assert result["run_rate"].isna().sum() == 0
        assert abs(float(result["run_rate"].iloc[-1]) - 8.0) < 0.01

    def test_stockout_days_excluded(self):
        """Les jours de rupture ne doivent pas influencer le run rate."""
        corrected = [10.0] * 30 + [0.0] * 5
        stockout = [False] * 30 + [True] * 5
        df = make_df(corrected, is_stockout=stockout)
        result = calculate_run_rate(df)
        last_run_rate = float(result["run_rate"].iloc[-1])
        assert last_run_rate > 5.0, f"Run rate biaisé par ruptures : {last_run_rate}"

    def test_outlier_days_excluded(self):
        """Les jours outlier ne doivent pas influencer le run rate."""
        corrected = [5.0] * 29 + [500.0] + [5.0] * 5
        outlier = [False] * 29 + [True] + [False] * 5
        df = make_df(corrected, is_outlier=outlier)
        result = calculate_run_rate(df)
        last_run_rate = float(result["run_rate"].iloc[-1])
        assert last_run_rate < 20.0, f"Run rate biaisé par outlier : {last_run_rate}"

    def test_custom_window(self):
        """Vérification avec une fenêtre personnalisée (7j)."""
        corrected = [5.0] * 30 + [20.0] * 7
        df = make_df(corrected)
        result = calculate_run_rate(df, window=7)
        last_run_rate = float(result["run_rate"].iloc[-1])
        assert abs(last_run_rate - 20.0) < 1.0

    def test_sorted_by_date(self):
        """Le résultat est trié par date croissante."""
        df = make_df([5.0] * 10)
        df = df.iloc[::-1].reset_index(drop=True)
        result = calculate_run_rate(df)
        assert result["date"].is_monotonic_increasing

    def test_missing_column_raises(self):
        """Une colonne manquante lève ValueError."""
        df = pd.DataFrame({"date": [date(2025, 1, 1)]})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            calculate_run_rate(df)

    def test_run_rate_window_constant(self):
        """La fenêtre par défaut est bien 30 jours."""
        assert RUN_RATE_WINDOW == 30

    def test_run_rate_min_periods_constant(self):
        """Le min_periods est bien 4."""
        assert RUN_RATE_MIN_PERIODS == 4


class TestCalculateRunRateBatch:

    def test_batch_two_products(self):
        """Traitement de deux produits indépendants."""
        df = pd.DataFrame({
            "product_id": ["p1"] * 35 + ["p2"] * 35,
            "date": list(pd.date_range("2025-01-01", periods=35)) * 2,
            "corrected_units_sold": [10.0] * 35 + [5.0] * 35,
        })
        result = calculate_run_rate_batch(df)
        assert set(result["product_id"].unique()) == {"p1", "p2"}
        assert "run_rate" in result.columns
        p1_rate = float(result[result["product_id"] == "p1"]["run_rate"].iloc[-1])
        p2_rate = float(result[result["product_id"] == "p2"]["run_rate"].iloc[-1])
        assert abs(p1_rate - 10.0) < 0.5
        assert abs(p2_rate - 5.0) < 0.5

    def test_batch_missing_product_id_raises(self):
        """Colonnes manquantes → ValueError."""
        df = pd.DataFrame({"date": [], "corrected_units_sold": []})
        with pytest.raises(ValueError, match="Colonnes manquantes"):
            calculate_run_rate_batch(df)
