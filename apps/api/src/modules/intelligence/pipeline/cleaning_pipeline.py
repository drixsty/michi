"""
Cleaning Pipeline — Sprint 21.

Orchestre le pipeline de nettoyage de la demande sans aucune dépendance DB.

Étapes :
    1. OOS Correction   → corrige les jours de rupture de stock
    2. IQR Detection    → détecte et corrige les outliers (upper-bound only)
    3. Run Rate         → calcule le run rate journalier

Entrée  : DataFrame brut avec colonnes attendues par chaque algorithme
Sortie  : DataFrame enrichi + run_rate (float)

Performance : O(n) — pipeline vectorisé.
"""

import pandas as pd

from modules.intelligence.algorithms import (
    correct_out_of_stock,
    detect_outliers,
    calculate_run_rate,
)


def run_cleaning_pipeline(
    df: pd.DataFrame,
    sku: str = "",
) -> tuple[pd.DataFrame, float, float]:
    """
    Applique le pipeline OOS → IQR → RunRate sur un DataFrame de demande brute.

    Args:
        df: DataFrame avec colonnes :
            - date (ou index DatetimeIndex)
            - units_sold (float)
            - end_of_day_stock (int)
        sku: Identifiant SKU pour les logs/debug (optionnel).

    Returns:
        Tuple (cleaned_df, run_rate, sigma) où :
        - cleaned_df: DataFrame enrichi avec colonnes supplémentaires
          (theoretical_units_sold, is_outlier, iqr_upper, iqr_lower,
           corrected_quantity, run_rate_series, demand_sigma)
        - run_rate: float — run rate journalier final
        - sigma: float — écart-type de la demande (volatilité)

    Raises:
        ValueError: si les colonnes requises sont absentes.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "date": pd.date_range("2024-01-01", periods=30),
        ...     "units_sold": [5.0] * 28 + [0.0, 0.0],
        ...     "end_of_day_stock": [10] * 28 + [0, 0],
        ... })
        >>> cleaned, rr = run_cleaning_pipeline(df, sku="SKU001")
        >>> rr > 0
        True
    """
    required_cols = {"units_sold", "end_of_day_stock"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"[CleaningPipeline] SKU={sku!r} — colonnes manquantes: {missing}"
        )

    # Étape 1 : correction OOS → ajoute theoretical_units_sold, is_stockout
    df_step1 = correct_out_of_stock(df.copy())

    # Étape 2 : détection + correction IQR → ajoute is_outlier, corrected_units_sold, iqr_*
    df_step2 = detect_outliers(df_step1)

    # Alias corrected_quantity = corrected_units_sold (interface publique du pipeline)
    corrected_col = (
        "corrected_units_sold"
        if "corrected_units_sold" in df_step2.columns
        else "units_sold"
    )
    df_step2["corrected_quantity"] = df_step2[corrected_col]

    # Étape 3 : calcul du run rate → ajoute colonne run_rate + is_trending
    df_step3 = calculate_run_rate(df_step2)

    # Extraire le run rate scalaire : médiane de la série (valeur stable, non-NaN)
    run_rate_series = df_step3["run_rate"].dropna()
    run_rate: float = float(run_rate_series.iloc[-1]) if len(run_rate_series) > 0 else 0.0

    # Extraire le sigma scalaire (volatilité) — Sprint 22 (DS v2)
    sigma_series = df_step3["demand_sigma"].dropna()
    sigma: float = float(sigma_series.iloc[-1]) if len(sigma_series) > 0 else 0.0

    return df_step3, run_rate, sigma
