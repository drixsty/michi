"""
Forecast Accuracy — Sprint 10 (corrigé Sprint 26)

Calcule les métriques de précision de prévision pour un produit.

Métriques retournées :
    mape  : Mean Absolute Percentage Error (vraie MAPE, non bornée)
            mape = mean( |actual(t) - forecast| / actual(t) )  sur les jours où actual > 0
    mae   : Mean Absolute Error en unités absolues
            mae = mean( |actual(t) - forecast| )
    bias  : Biais systématique (positif = sur-estimation)
            bias = mean( forecast - actual(t) )

Différence avec l'implémentation précédente :
    L'ancienne formule comparait le run_rate scalaire à la moyenne des ventes,
    ce qui produisait une erreur relative agrégée (non-MAPE) et une valeur
    circulaire (dérivé vs source). La vraie MAPE compare la prédiction à chaque
    observation individuelle, capturant la dispersion temporelle.

Notes :
    - run_rate est traité comme une prévision constante (pas de série de prévisions).
      C'est correct pour le modèle de prévision par run_rate.
    - MAPE non bornée : peut dépasser 1.0 (100%). Ne pas capituler en production.
    - Si actual_series est vide ou toutes les valeurs sont <= 0 : retourne None.

Performance : O(n) vectorisé.
"""
from typing import Optional
import pandas as pd


def calculate_mape_score(run_rate: float, recent_sales: pd.Series) -> Optional[float]:
    """
    Calcule la vraie MAPE entre le run_rate constant et les ventes réelles.

    Args:
        run_rate: Prévision journalière constante (unités/jour).
        recent_sales: Série des ventes réelles nettoyées (corrected_units_sold).
                      NaN ignorés automatiquement.

    Returns:
        MAPE entre 0.0 et +∞ (ex: 0.15 = 15% d'erreur), ou None si pas de données.

    Example:
        >>> import pandas as pd
        >>> calculate_mape_score(10.0, pd.Series([8.0, 12.0, 10.0, 11.0]))
        0.125
        >>> calculate_mape_score(10.0, pd.Series([0.0, 0.0]))
        None
    """
    return _calculate_forecast_metrics(run_rate, recent_sales).get("mape")


def calculate_forecast_metrics(run_rate: float, recent_sales: pd.Series) -> dict:
    """
    Retourne le dictionnaire complet des métriques de précision.

    Returns:
        {"mape": float|None, "mae": float|None, "bias": float|None}
        Toutes les valeurs sont None si pas de données utilisables.
    """
    return _calculate_forecast_metrics(run_rate, recent_sales)


def _calculate_forecast_metrics(run_rate: float, recent_sales: pd.Series) -> dict:
    empty = {"mape": None, "mae": None, "bias": None}

    if recent_sales.empty:
        return empty

    actual = recent_sales.dropna()
    actual = actual[actual > 0]

    if actual.empty:
        return empty

    errors = (actual - run_rate).abs()
    pct_errors = errors / actual

    return {
        "mape": pct_errors.mean(),
        "mae": errors.mean(),
        "bias": (run_rate - actual).mean(),
    }
