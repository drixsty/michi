import pandas as pd
import numpy as np
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

RUN_RATE_WINDOW = 30     # jours pour la médiane glissante du run rate
RUN_RATE_MIN_PERIODS = 4  # minimum de jours valides pour un run rate fiable


def calculate_run_rate(df: pd.DataFrame, window: int = RUN_RATE_WINDOW) -> pd.DataFrame:
    """
    Calcule le run rate journalier avec détection adaptative de tendance (Sprint 15).
    
    L'algorithme utilise une médiane glissante, mais réduit dynamiquement la fenêtre
    si une accélération forte est détectée (momentum), permettant de capturer
    la saisonnalité ou les tendances de croissance sans l'inertie du 30j.
    """
    required = {"date", "corrected_units_sold"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    df = df.sort_values("date").copy()

    # 1. Masquer les jours non fiables
    valid_mask = pd.Series(True, index=df.index)
    if "is_stockout" in df.columns:
        valid_mask &= ~df["is_stockout"]
    if "is_outlier" in df.columns:
        valid_mask &= ~df["is_outlier"]

    clean_sales = df["corrected_units_sold"].where(valid_mask)

    # 2. Calcul du Momentum (tendance court terme vs moyen terme)
    # On compare la moyenne 7j à la moyenne 30j
    short_term = clean_sales.rolling(window=7, min_periods=2).mean()
    medium_term = clean_sales.rolling(window=30, min_periods=4).mean()
    
    # Facteur de tendance : > 1 si croissance, < 1 si déclin
    momentum = (short_term / medium_term.replace(0, np.nan)).fillna(1.0)
    
    # 3. Fenêtre Adaptative
    # Si momentum > 1.2 (croissance > 20%), on bascule sur une fenêtre de 7j pour être réactif
    # Sinon on reste sur 30j pour la stabilité
    is_trending = momentum > 1.2
    
    run_rate_30j = clean_sales.rolling(window=30, min_periods=4).median()
    run_rate_7j = clean_sales.rolling(window=7, min_periods=2).median()
    
    # Mixage : run_rate_7j si trending, sinon run_rate_30j
    adaptive_run_rate = run_rate_30j.copy()
    adaptive_run_rate[is_trending] = run_rate_7j[is_trending]

    # 4. Fallback Global
    global_median = clean_sales.dropna().median()
    if pd.isna(global_median):
        global_median = df["corrected_units_sold"].median()
    if pd.isna(global_median):
        global_median = 0.0

    df["run_rate"] = adaptive_run_rate.fillna(global_median).clip(lower=0.0)
    
    # Ajout du diagnostic (invisible au frontend mais utile pour l'audit)
    df["is_trending"] = is_trending

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
