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


# ---------------------------------------------------------------------------
# Tests DOW seasonality (Sprint 27)
# ---------------------------------------------------------------------------

from modules.intelligence.algorithms.seasonality import calculate_weekly_indices


class TestCalculateWeeklyIndices:

    def test_uniform_sales_all_factors_one(self) -> None:
        """Ventes uniformes → tous les facteurs = 1.0."""
        dow = pd.Series(list(range(7)) * 4)   # 4 semaines complètes
        values = pd.Series([10.0] * 28)
        idx = calculate_weekly_indices(dow, values)
        for d in range(7):
            assert abs(idx[d] - 1.0) < 1e-9, f"DOW {d}: attendu 1.0, obtenu {idx[d]}"

    def test_monday_double_sales(self) -> None:
        """Lundi (DOW=0) avec 2× les ventes → facteur ≈ 1.75 (7 DOWs, 1 à 2× les autres)."""
        # Lundi = 2.0, autres = 1.0 → grand_mean = (2 + 6*1) / 7 = 1.143
        # facteur_lundi = 2.0 / 1.143 ≈ 1.75
        daily = [2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        dow = pd.Series(list(range(7)) * 4)
        values = pd.Series(daily * 4)
        idx = calculate_weekly_indices(dow, values)
        assert idx[0] > 1.3, f"Lundi devrait être > 1.3, obtenu {idx[0]:.3f}"
        assert idx[1] < 1.0, f"Mardi devrait être < 1.0, obtenu {idx[1]:.3f}"

    def test_factors_normalize_to_mean_one(self) -> None:
        """La moyenne des facteurs doit toujours être ≈ 1.0."""
        daily = [3.0, 1.5, 2.0, 1.0, 2.5, 0.5, 1.0]
        dow = pd.Series(list(range(7)) * 8)
        values = pd.Series(daily * 8)
        idx = calculate_weekly_indices(dow, values)
        mean_factor = sum(idx.values()) / 7
        assert abs(mean_factor - 1.0) < 1e-9, f"Moyenne facteurs: {mean_factor:.6f}"

    def test_insufficient_data_returns_all_ones(self) -> None:
        """< 14 observations → fallback {0..6: 1.0}."""
        dow = pd.Series([0, 1, 2, 3, 4, 5, 6])
        values = pd.Series([5.0, 8.0, 3.0, 6.0, 9.0, 2.0, 4.0])
        idx = calculate_weekly_indices(dow, values)
        assert all(v == 1.0 for v in idx.values()), f"Attendu all 1.0, obtenu {idx}"

    def test_dow_normalization_removes_calendar_bias(self) -> None:
        """Le run rate normalisé DOW est stable quel que soit le profil calendaire."""
        # Produit avec forte saisonnalité Lundi : 50u, autres : 10u
        # 35 jours démarrant un Lundi (01/01/2025 = Mercredi, prenons 06/01 = Lundi)
        start = date(2025, 1, 6)  # Lundi
        n = 35
        dates = [start + timedelta(days=i) for i in range(n)]
        sales = [50.0 if (start + timedelta(days=i)).weekday() == 0 else 10.0 for i in range(n)]
        df = pd.DataFrame({"date": dates, "corrected_units_sold": sales})
        result = make_df(sales, start=start)
        result_rr = calculate_run_rate(result)
        rr_final = float(result_rr["run_rate"].iloc[-1])
        # La moyenne réelle = (50 + 10*6)/7 ≈ 15.71 u/j
        expected = (50.0 + 10.0 * 6) / 7
        # Avec normalisation DOW, le run rate doit être proche de la vraie moyenne
        assert abs(rr_final - expected) < 3.0, f"run_rate={rr_final:.2f} loin de {expected:.2f}"
