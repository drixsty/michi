"""
Run Rate Algorithm — US 2.5 (Sprint 4)

Objectif :
    Calculer le taux de vente quotidien moyen (run rate) sur une fenêtre glissante
    de 30 jours à partir des ventes nettoyées (corrected_units_sold post-OOS et post-IQR).

Formule :
    run_rate[j] = median(corrected_units_sold[j-29..j] pour les jours non-rupture)

    La médiane est préférée à la moyenne pour la robustesse aux outliers résiduels.
    Si < 4 jours non-rupture dans la fenêtre : fallback médiane globale de la série.

Hypothèses :
    - L'entrée contient ``corrected_units_sold`` (post-nettoyage complet)
    - Un seul produit par appel à ``calculate_run_rate``
    - La fenêtre de 30 jours est calibrée pour capturer la tendance récente
      sans être trop sensible au bruit court-terme (7j) ni trop lente (90j)

Performance :
    O(n) — vectorisation Pandas, pas de boucles for.
"""
import pandas as pd
import numpy as np

RUN_RATE_WINDOW = 30     # jours pour la médiane glissante du run rate
RUN_RATE_MIN_PERIODS = 4  # minimum de jours valides pour un run rate fiable


def calculate_run_rate(df: pd.DataFrame, window: int = RUN_RATE_WINDOW) -> pd.DataFrame:
    """
    Calcule le run rate journalier sur une fenêtre glissante pour un seul produit.

    Args:
        df: DataFrame avec colonnes [date, corrected_units_sold].
            La colonne ``is_stockout`` est utilisée si présente pour exclure
            les jours de rupture du calcul (demand not observed).
            La colonne ``is_outlier`` est utilisée si présente pour exclure
            les outliers non corrigés.
        window: Fenêtre en jours pour la médiane glissante (défaut: 30).

    Returns:
        DataFrame enrichi avec :
        - ``run_rate`` (float) : taux de vente quotidien moyen sur ``window`` jours.
          Toujours >= 0. NaN si insuffisamment de données ET pas de fallback global.

    Raises:
        ValueError: Si les colonnes requises sont manquantes.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "date": pd.date_range("2025-01-01", periods=35),
        ...     "corrected_units_sold": [10.0] * 35,
        ... })
        >>> result = calculate_run_rate(df)
        >>> float(result["run_rate"].iloc[-1])
        10.0
    """
    required = {"date", "corrected_units_sold"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    df = df.sort_values("date").copy()

    # Masquer les jours non fiables pour le calcul du run rate
    valid_mask = pd.Series(True, index=df.index)
    if "is_stockout" in df.columns:
        valid_mask &= ~df["is_stockout"]
    if "is_outlier" in df.columns:
        valid_mask &= ~df["is_outlier"]

    # Série nettoyée — NaN sur les jours invalides
    clean_sales = df["corrected_units_sold"].where(valid_mask)

    # Médiane glissante sur ``window`` jours
    rolling_run_rate = (
        clean_sales
        .rolling(window=window, min_periods=RUN_RATE_MIN_PERIODS)
        .median()
    )

    # Fallback : médiane globale des jours valides
    global_median = clean_sales.dropna().median()
    if pd.isna(global_median):
        global_median = df["corrected_units_sold"].median()
    if pd.isna(global_median):
        global_median = 0.0

    df["run_rate"] = rolling_run_rate.fillna(global_median).clip(lower=0.0)

    return df


def calculate_run_rate_batch(df: pd.DataFrame, window: int = RUN_RATE_WINDOW) -> pd.DataFrame:
    """
    Applique le calcul de run rate sur un DataFrame multi-produits.

    Args:
        df: DataFrame avec colonnes [product_id, date, corrected_units_sold].
            Peut contenir ``is_stockout`` et ``is_outlier``.
        window: Fenêtre en jours pour la médiane glissante (défaut: 30).

    Returns:
        DataFrame enrichi avec ``run_rate``.
    """
    required = {"product_id", "date", "corrected_units_sold"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    result = (
        df.groupby("product_id", group_keys=False)
        .apply(lambda g: calculate_run_rate(g, window=window))
        .reset_index(drop=True)
    )
    return result
