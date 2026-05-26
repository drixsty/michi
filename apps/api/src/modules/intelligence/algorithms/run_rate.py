"""
Run Rate Algorithm — US 2.5 (Sprint 4, corrigé Sprint 26-27)

Objectif :
    Calculer le taux de vente quotidien moyen (run rate) sur une fenêtre glissante
    de 30 jours propres (non-stockout, non-outlier) à partir des ventes nettoyées.

Corrections Sprint 26 :
    - Rolling sur valeurs propres uniquement (plus sur la série masquée NaN).
    - Blend progressif momentum (remplace le hard switch à 1.2).

Correction Sprint 27 — normalisation calendaire (DOW) :
    Problème : si les 30 derniers jours contiennent 5 lundis (gros jour) et 4 dimanches
    (petit jour), la médiane glissante est systématiquement biaisée vers le haut.
    Fix : avant le rolling, on divise chaque vente par l'indice du jour de la semaine
    (calculate_weekly_indices de seasonality.py). La médiane glissante est ainsi calculée
    sur une série « jour-moyen équivalent ». Résultat = run rate stable, sans biais
    calendaire, même pour les catégories à forte variation Lun-Dim (mode, loisirs, etc.).

    Condition d'activation : >= 14 observations nettes (2 semaines complètes minimum).
    En dessous, les facteurs DOW sont trop bruités → fallback non normalisé.

Formule run rate finale :
    clean_values  = corrected_units_sold filtré (non-stockout, non-outlier)
    norm_clean    = clean_values / dow_factor[weekday]   (si >= 14 obs)
    rr_30j[j]     = median(norm_clean[-30:])
    rr_7j[j]      = median(norm_clean[-7:])
    alpha         = clip((momentum - 1.0) / 0.5, 0, 1)
    run_rate[j]   = (1 - alpha) × rr_30j + alpha × rr_7j
    Fallback      : médiane globale de norm_clean si < 4 observations.

Performance : O(n) — vectorisation Pandas, pas de boucles for.
"""
import pandas as pd
import numpy as np
from .seasonality import calculate_weekly_indices

RUN_RATE_WINDOW = 30
RUN_RATE_MIN_PERIODS = 4


def calculate_run_rate(df: pd.DataFrame, window: int = RUN_RATE_WINDOW) -> pd.DataFrame:
    """
    Calcule le run rate journalier avec blend adaptatif de tendance.

    Args:
        df: DataFrame trié par date, une ligne par jour, un seul produit.
            Colonnes requises : [date, corrected_units_sold].
            Colonnes optionnelles : [is_stockout, is_outlier].
        window: Fenêtre en jours propres pour la médiane longue (défaut : 30).

    Returns:
        DataFrame enrichi avec [run_rate, demand_sigma, is_trending].
    """
    required = {"date", "corrected_units_sold"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    df = df.sort_values("date").copy()

    # 1. Masque des jours propres
    valid_mask = pd.Series(True, index=df.index)
    if "is_stockout" in df.columns:
        valid_mask &= ~df["is_stockout"]
    if "is_outlier" in df.columns:
        valid_mask &= ~df["is_outlier"]

    # 2. Sous-série propre pour les rolling (fix NaN-window)
    # Rolling sur clean_values garantit que window=30 = 30 vraies observations,
    # pas 30 positions calendaires dont 26 seraient NaN.
    clean_values = df.loc[valid_mask, "corrected_units_sold"]

    # 2b. Normalisation calendaire (DOW) — Sprint 27
    # Supprime le biais jour-de-semaine avant le rolling pour obtenir un run rate
    # stable quel que soit le profil calendaire de la fenêtre d'observation.
    # Activée seulement si >= 14 observations (2 semaines) : en dessous, les
    # facteurs DOW sont trop bruités et introduiraient plus de variance qu'ils n'en enlèvent.
    if len(clean_values) >= 14:
        clean_dow = pd.to_datetime(df.loc[valid_mask, "date"]).dt.dayofweek
        dow_factors = calculate_weekly_indices(clean_dow, clean_values)
        dow_adj = clean_dow.map(dow_factors).replace(0.0, 1.0)
        norm_clean = clean_values / dow_adj
    else:
        norm_clean = clean_values

    if len(clean_values) >= RUN_RATE_MIN_PERIODS:
        rr_30j = (
            norm_clean.rolling(window=window, min_periods=RUN_RATE_MIN_PERIODS)
            .median()
            .reindex(df.index)
            .ffill()
        )
        rr_7j = (
            norm_clean.rolling(window=7, min_periods=2)
            .median()
            .reindex(df.index)
            .ffill()
        )
        short_term = (
            norm_clean.rolling(window=7, min_periods=2)
            .mean()
            .reindex(df.index)
            .ffill()
        )
        medium_term = (
            norm_clean.rolling(window=window, min_periods=RUN_RATE_MIN_PERIODS)
            .mean()
            .reindex(df.index)
            .ffill()
        )
        sigma_30j = (
            norm_clean.rolling(window=window, min_periods=RUN_RATE_MIN_PERIODS)
            .std()
            .reindex(df.index)
            .ffill()
        )
    else:
        nan_series = pd.Series(np.nan, index=df.index)
        rr_30j = nan_series.copy()
        rr_7j = nan_series.copy()
        short_term = nan_series.copy()
        medium_term = nan_series.copy()
        sigma_30j = nan_series.copy()

    # 3. Momentum et blend progressif
    momentum = (short_term / medium_term.replace(0, np.nan)).fillna(1.0)
    # alpha ∈ [0, 1] : 0 = pur 30j, 1 = pur 7j (atteint à momentum >= 1.5)
    alpha = ((momentum - 1.0) / 0.5).clip(0.0, 1.0)
    is_trending = momentum > 1.2

    adaptive_run_rate = (1.0 - alpha) * rr_30j + alpha * rr_7j

    # 4. Fallback global (sur série normalisée pour cohérence)
    global_median = norm_clean.median() if len(norm_clean) > 0 else 0.0
    if pd.isna(global_median) or global_median == 0.0:
        non_zero = df.loc[df["corrected_units_sold"] > 0, "corrected_units_sold"]
        global_median = non_zero.median() if not non_zero.empty else 0.0
    if pd.isna(global_median):
        global_median = 0.0

    df["run_rate"] = adaptive_run_rate.fillna(global_median).clip(lower=0.0)

    # 5. Sigma (volatilité demande, sur série normalisée : cohérent avec le run rate)
    global_std = norm_clean.std() if len(norm_clean) > 1 else 0.0
    if pd.isna(global_std):
        global_std = 0.0

    df["demand_sigma"] = sigma_30j.fillna(global_std).fillna(0.0).clip(lower=0.0)
    df["is_trending"] = is_trending

    return df


def calculate_run_rate_batch(df: pd.DataFrame, window: int = RUN_RATE_WINDOW) -> pd.DataFrame:
    """
    Applique le calcul de run rate sur un DataFrame multi-produits.

    Args:
        df: DataFrame avec colonnes [product_id, date, corrected_units_sold].
            Peut contenir [is_stockout, is_outlier].
        window: Fenêtre en jours propres (défaut : 30).

    Returns:
        DataFrame enrichi avec [run_rate, demand_sigma, is_trending].
    """
    required = {"product_id", "date", "corrected_units_sold"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    return (
        df.groupby("product_id", group_keys=False)
        .apply(lambda g: calculate_run_rate(g, window=window))
        .reset_index(drop=True)
    )
