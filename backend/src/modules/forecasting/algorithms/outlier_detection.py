"""
Outlier Detection Algorithm — US 2.2 (Méthode IQR)

Objectif :
    Détecter et corriger les pics de ventes anormaux (ex : erreurs de saisie,
    doublons de commandes) tout en CONSERVANT les vrais pics saisonniers
    (Black Friday, soldes) qui font partie de la demande réelle.

Formule IQR :
    Q1 = 25e percentile des ventes non-rupture
    Q3 = 75e percentile des ventes non-rupture
    IQR = Q3 - Q1
    borne_haute = Q3 + 1.5 × IQR
    borne_basse = max(0, Q1 - 1.5 × IQR)   # jamais négatif

    Un jour est outlier si :
        units_sold > borne_haute  OU  units_sold < borne_basse
        ET ce n'est PAS un jour de rupture (is_stockout = False)

Correction :
    Les outliers sont remplacés par la médiane glissante sur 7 jours
    des jours NON-outlier, NON-rupture précédents.
    Fallback : médiane globale de la série.

Hypothèses :
    - Les ruptures (is_stockout=True) ne sont JAMAIS flaggées outlier
    - La colonne ``theoretical_units_sold`` (post-OOS) est utilisée si disponible,
      sinon ``units_sold``
    - Un seul produit par appel à ``detect_outliers``

Performance :
    O(n) — pas de boucles for.
"""
import pandas as pd
import numpy as np

OUTLIER_ROLLING_WINDOW = 7   # jours pour la médiane glissante de correction


def detect_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte et corrige les outliers pour un seul produit.

    Args:
        df: DataFrame avec colonnes [date, units_sold, end_of_day_stock].
            La colonne ``is_stockout`` est utilisée si présente,
            sinon recalculée depuis ``end_of_day_stock``.
            La colonne ``theoretical_units_sold`` est utilisée si présente.

    Returns:
        DataFrame enrichi avec :
        - ``is_outlier`` (bool)
        - ``iqr_lower`` (float) : borne basse IQR
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

    # Calcul IQR sur jours non-rupture uniquement
    non_stockout = reference[~df["is_stockout"]]

    if len(non_stockout) < 4:
        # Pas assez de données pour l'IQR — on ne flagge rien
        df["is_outlier"] = False
        df["iqr_lower"] = np.nan
        df["iqr_upper"] = np.nan
        df["corrected_units_sold"] = reference
        return df

    q1 = non_stockout.quantile(0.25)
    q3 = non_stockout.quantile(0.75)
    iqr = q3 - q1

    lower = max(0.0, float(q1 - 1.5 * iqr))
    upper = float(q3 + 1.5 * iqr)

    df["iqr_lower"] = lower
    df["iqr_upper"] = upper

    # Flaguer les outliers (jamais les jours de rupture)
    df["is_outlier"] = (
        (~df["is_stockout"]) &
        ((reference < lower) | (reference > upper))
    )

    # Médiane glissante 7j sur jours non-outlier, non-rupture pour la correction
    clean_series = reference.where(~df["is_outlier"] & ~df["is_stockout"])
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


def detect_outliers_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique la détection IQR sur un DataFrame multi-produits.

    Args:
        df: DataFrame avec colonnes [product_id, date, units_sold, end_of_day_stock].
            Peut contenir ``is_stockout`` et ``theoretical_units_sold`` (post-OOS).

    Returns:
        DataFrame enrichi avec ``is_outlier`` et ``corrected_units_sold``.
    """
    required = {"product_id", "date", "units_sold", "end_of_day_stock"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    result = (
        df.groupby("product_id", group_keys=False)
        .apply(detect_outliers)
        .reset_index(drop=True)
    )
    return result
