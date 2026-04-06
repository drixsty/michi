"""
Outlier Detection Algorithm — US 2.2 (Méthode IQR, révisé Sprint 4 — DS-2)

Objectif :
    Détecter et corriger les pics de ventes anormaux (ex : erreurs de saisie,
    doublons de commandes) tout en CONSERVANT les vrais pics saisonniers
    (Black Friday, soldes) qui font partie de la demande réelle.

Formule IQR :
    Q1 = 25e percentile des ventes non-rupture (sur fenêtre iqr_window ou global)
    Q3 = 75e percentile des ventes non-rupture
    IQR = Q3 - Q1
    borne_haute = Q3 + 1.5 × IQR
    borne_basse = max(0, Q1 - 1.5 × IQR)   # jamais négatif

    Un jour est outlier si :
        units_sold > borne_haute  OU  units_sold < borne_basse
        ET ce n'est PAS un jour de rupture (is_stockout = False)

Changement Sprint 4 (DS-2) :
    Ajout du paramètre ``iqr_window`` à ``detect_outliers()``.
    - None (défaut) : IQR global sur toute la série (comportement Sprint 3)
    - int (ex: 90) : IQR glissant sur une fenêtre de N jours
    Justification : un IQR global flagge à tort les ventes hivernales d'un produit
    à forte saisonnalité estivale. L'IQR glissant calcule les bornes localement.

Correction :
    Les outliers sont remplacés par la médiane glissante sur 7 jours
    des jours NON-outlier, NON-rupture précédents.
    Fallback : médiane globale de la série.

Hypothèses :
    - Les ruptures (is_stockout=True) ne sont JAMAIS flaggées outlier
    - La colonne ``theoretical_units_sold`` (post-OOS) est utilisée si disponible,
      sinon ``units_sold``
    - Un seul produit par appel à ``detect_outliers``

Limite connue :
    L'IQR glissant (iqr_window=90) réduit les faux positifs saisonniers mais
    peut manquer des outliers en début de série (<90j de données disponibles).
    Pour une modélisation saisonnière complète, préférer STL (backlog post-MVP).

Performance :
    O(n) — pas de boucles for.
"""
import pandas as pd
import numpy as np

OUTLIER_ROLLING_WINDOW = 7    # jours pour la médiane glissante de correction
IQR_GLOBAL_WINDOW = None      # défaut : IQR calculé sur toute la série
IQR_SEASONAL_WINDOW = 90      # fenêtre recommandée pour produits saisonniers


def detect_outliers(df: pd.DataFrame, iqr_window: int | None = None) -> pd.DataFrame:
    """
    Détecte et corrige les outliers pour un seul produit.

    Args:
        df: DataFrame avec colonnes [date, units_sold, end_of_day_stock].
            La colonne ``is_stockout`` est utilisée si présente,
            sinon recalculée depuis ``end_of_day_stock``.
            La colonne ``theoretical_units_sold`` est utilisée si présente.
        iqr_window: Fenêtre en jours pour l'IQR glissant (DS-2 Sprint 4).
            - None (défaut) : IQR global sur toute la série.
            - int (ex: 90) : IQR recalculé sur une fenêtre glissante de N jours.
              Recommandé pour les produits à forte saisonnalité.

    Returns:
        DataFrame enrichi avec :
        - ``is_outlier`` (bool)
        - ``iqr_lower`` (float) : borne basse IQR (locale si iqr_window, globale sinon)
        - ``iqr_upper`` (float) : borne haute IQR
        - ``corrected_units_sold`` (float) : ventes finales après correction outlier

    Raises:
        ValueError: Si les colonnes requises sont manquantes.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "date": pd.date_range("2025-01-01", periods=10),
        ...     "units_sold": [5.0]*9 + [500.0],   # outlier évident
        ...     "end_of_day_stock": [100]*10,
        ... })
        >>> result = detect_outliers(df)
        >>> result["is_outlier"].iloc[-1]
        True
    """
    required = {"date", "units_sold", "end_of_day_stock"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    df = df.sort_values("date").copy()

    # Utiliser is_stockout si déjà calculé, sinon le recalculer
    if "is_stockout" not in df.columns:
        df["is_stockout"] = df["end_of_day_stock"] == 0

    # Série de référence : theoretical si disponible, sinon units_sold
    ref_col = "theoretical_units_sold" if "theoretical_units_sold" in df.columns else "units_sold"
    reference = df[ref_col]

    # Ventes non-rupture pour le calcul IQR
    non_stockout_mask = ~df["is_stockout"]
    non_stockout = reference[non_stockout_mask]

    if len(non_stockout) < 4:
        df["is_outlier"] = False
        df["iqr_lower"] = np.nan
        df["iqr_upper"] = np.nan
        df["corrected_units_sold"] = reference
        return df

    if iqr_window is None:
        # ── IQR global (comportement par défaut) ─────────────────────────────
        q1 = float(non_stockout.quantile(0.25))
        q3 = float(non_stockout.quantile(0.75))
        iqr = q3 - q1
        lower_series = pd.Series(max(0.0, q1 - 1.5 * iqr), index=df.index)
        upper_series = pd.Series(q3 + 1.5 * iqr, index=df.index)
    else:
        # ── IQR glissant (DS-2) ───────────────────────────────────────────────
        # Masquer les jours de rupture avant le calcul glissant
        clean_ref = reference.where(non_stockout_mask)
        q1_roll = clean_ref.rolling(window=iqr_window, min_periods=4).quantile(0.25)
        q3_roll = clean_ref.rolling(window=iqr_window, min_periods=4).quantile(0.75)
        iqr_roll = q3_roll - q1_roll
        lower_series = (q1_roll - 1.5 * iqr_roll).clip(lower=0.0)
        upper_series = q3_roll + 1.5 * iqr_roll
        # Remplir les NaN en début de série par l'IQR global
        q1_global = float(non_stockout.quantile(0.25))
        q3_global = float(non_stockout.quantile(0.75))
        iqr_global = q3_global - q1_global
        lower_series = lower_series.fillna(max(0.0, q1_global - 1.5 * iqr_global))
        upper_series = upper_series.fillna(q3_global + 1.5 * iqr_global)

    df["iqr_lower"] = lower_series
    df["iqr_upper"] = upper_series

    # Flaguer les outliers (jamais les jours de rupture)
    df["is_outlier"] = (
        non_stockout_mask &
        ((reference < lower_series) | (reference > upper_series))
    )

    # Médiane glissante 7j sur jours propres pour la correction
    clean_series = reference.where(~df["is_outlier"] & non_stockout_mask)
    rolling_median = (
        clean_series
        .rolling(window=OUTLIER_ROLLING_WINDOW, min_periods=1)
        .median()
    )

    # Fallback : médiane globale
    global_median = non_stockout[~df.loc[non_stockout.index, "is_outlier"]].median()
    if pd.isna(global_median):
        global_median = non_stockout.median()
    if pd.isna(global_median):
        global_median = 0.0

    # Appliquer correction
    df["corrected_units_sold"] = reference.copy()
    outlier_mask = df["is_outlier"]
    correction = rolling_median.where(outlier_mask).fillna(global_median)
    df.loc[outlier_mask, "corrected_units_sold"] = correction[outlier_mask]
    df["corrected_units_sold"] = df["corrected_units_sold"].clip(lower=0.0)

    return df


def detect_outliers_batch(df: pd.DataFrame, iqr_window: int | None = None) -> pd.DataFrame:
    """
    Applique la détection IQR sur un DataFrame multi-produits.

    Args:
        df: DataFrame avec colonnes [product_id, date, units_sold, end_of_day_stock].
            Peut contenir ``is_stockout`` et ``theoretical_units_sold`` (post-OOS).
        iqr_window: Fenêtre IQR glissante en jours (None = IQR global).
            Voir ``detect_outliers()`` pour le détail.

    Returns:
        DataFrame enrichi avec ``is_outlier`` et ``corrected_units_sold``.
    """
    required = {"product_id", "date", "units_sold", "end_of_day_stock"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    result = (
        df.groupby("product_id", group_keys=False)
        .apply(lambda g: detect_outliers(g, iqr_window=iqr_window))
        .reset_index(drop=True)
    )
    return result
