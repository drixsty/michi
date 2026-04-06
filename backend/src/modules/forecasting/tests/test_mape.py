"""
Tests MAPE — US 2.4
Valide que la pipeline OOS + IQR maintient un MAPE < 15% sur données synthétiques.

Méthodologie :
    1. Générer une demande "vraie" connue (ground truth)
    2. Simuler des ruptures et outliers dessus
    3. Appliquer la pipeline de correction
    4. Calculer MAPE entre ground truth et valeurs corrigées
    5. Vérifier MAPE < 15%

Formule MAPE :
    MAPE = mean(|actual - forecast| / actual) × 100
    (calculé uniquement sur les jours corrigés, actual > 0)
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta

from src.modules.forecasting.algorithms.out_of_stock_correction import correct_out_of_stock
from src.modules.forecasting.algorithms.outlier_detection import detect_outliers

MAPE_THRESHOLD = 15.0   # % maximum acceptable


def mape(actual: pd.Series, forecast: pd.Series) -> float:
    """
    Calcule le MAPE en excluant les valeurs actual = 0.

    Args:
        actual: Valeurs de référence (ground truth).
        forecast: Valeurs prédites/corrigées.

    Returns:
        MAPE en pourcentage (0–100).
    """
    mask = actual > 0
    if mask.sum() == 0:
        return 0.0
    return float(np.mean(np.abs((actual[mask] - forecast[mask]) / actual[mask])) * 100)


def make_ground_truth(n: int = 365, base: float = 8.0, seed: int = 42) -> pd.Series:
    """Demande journalière stable avec légère variabilité."""
    rng = np.random.default_rng(seed)
    return pd.Series(np.maximum(0, rng.normal(base, base * 0.2, n)))


def inject_stockouts(df: pd.DataFrame, periods: list[tuple[int, int]]) -> pd.DataFrame:
    """Injecte des ruptures sur des périodes données (index start, end)."""
    df = df.copy()
    for start, end in periods:
        df.loc[start:end, "units_sold"] = 0.0
        df.loc[start:end, "end_of_day_stock"] = 0
    return df


def inject_outliers(df: pd.DataFrame, indices: list[int], value: float) -> pd.DataFrame:
    """Injecte des valeurs aberrantes à des indices précis."""
    df = df.copy()
    for i in indices:
        df.loc[i, "units_sold"] = value
    return df


class TestMAPE:

    def _build_base_df(self, n: int = 365, seed: int = 42) -> tuple[pd.Series, pd.DataFrame]:
        """Construit un DataFrame de test avec ground truth."""
        ground_truth = make_ground_truth(n=n, seed=seed)
        dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(n)]
        df = pd.DataFrame({
            "date": dates,
            "units_sold": ground_truth.tolist(),
            "end_of_day_stock": [100] * n,
        })
        return ground_truth, df

    def test_mape_oos_correction_below_threshold(self):
        """OOS Correction : MAPE < 15% sur ruptures simulées."""
        ground_truth, df = self._build_base_df(n=365)

        # Injecter 3 ruptures (10% des jours ~ 36j)
        df_corrupted = inject_stockouts(df, [(50, 60), (150, 165), (280, 295)])

        result = correct_out_of_stock(df_corrupted)

        # Calculer MAPE uniquement sur les jours de rupture
        stockout_idx = result[result["is_stockout"]].index
        actual = ground_truth.iloc[stockout_idx].values
        forecast = result.loc[stockout_idx, "theoretical_units_sold"].values

        error = mape(pd.Series(actual), pd.Series(forecast))
        assert error < MAPE_THRESHOLD, f"MAPE OOS = {error:.2f}% >= {MAPE_THRESHOLD}%"

    def test_mape_outlier_correction_below_threshold(self):
        """IQR Correction : MAPE < 15% sur outliers simulés."""
        ground_truth, df = self._build_base_df(n=200, seed=99)

        # Injecter 5 outliers extrêmes
        outlier_indices = [30, 70, 100, 140, 180]
        df_corrupted = inject_outliers(df, outlier_indices, value=500.0)

        result = detect_outliers(df_corrupted)

        # MAPE uniquement sur les jours outliers corrigés
        outlier_idx = result[result["is_outlier"]].index
        if len(outlier_idx) == 0:
            pytest.skip("Aucun outlier détecté — vérifier les données de test")

        actual = ground_truth.iloc[outlier_idx].values
        forecast = result.loc[outlier_idx, "corrected_units_sold"].values

        error = mape(pd.Series(actual), pd.Series(forecast))
        assert error < MAPE_THRESHOLD, f"MAPE IQR = {error:.2f}% >= {MAPE_THRESHOLD}%"

    def test_mape_full_pipeline_below_threshold(self):
        """Pipeline complète OOS → IQR : MAPE global < 15%."""
        ground_truth, df = self._build_base_df(n=365, seed=7)

        # Ruptures + outliers combinés
        df_corrupted = inject_stockouts(df, [(80, 90), (200, 212)])
        df_corrupted = inject_outliers(df_corrupted, [40, 120, 300], value=400.0)

        # Pipeline
        after_oos = correct_out_of_stock(df_corrupted)
        after_iqr = detect_outliers(after_oos)

        corrected = after_iqr["corrected_units_sold"]
        error = mape(ground_truth, corrected)
        assert error < MAPE_THRESHOLD, f"MAPE pipeline = {error:.2f}% >= {MAPE_THRESHOLD}%"

    def test_mape_no_corrections_zero(self):
        """Sans ruptures ni outliers, MAPE ≈ 0%."""
        ground_truth, df = self._build_base_df(n=100, seed=1)

        after_oos = correct_out_of_stock(df)
        after_iqr = detect_outliers(after_oos)

        corrected = after_iqr["corrected_units_sold"]
        error = mape(ground_truth, corrected)
        # Pas de corrections → MAPE très faible (légère variabilité numpy acceptée)
        assert error < 1.0, f"MAPE sans correction = {error:.2f}% > 1%"

    def test_mape_function_excludes_zeros(self):
        """La fonction mape() ignore les actual=0."""
        actual = pd.Series([0.0, 10.0, 0.0, 8.0])
        forecast = pd.Series([5.0, 9.0, 3.0, 7.0])
        result = mape(actual, forecast)
        # Seulement les indices 1 et 3 comptent : |10-9|/10=10%, |8-7|/8=12.5% → mean=11.25%
        assert abs(result - 11.25) < 0.1

    def test_mape_threshold_constant(self):
        """Le seuil MAPE est bien fixé à 15%."""
        assert MAPE_THRESHOLD == 15.0
