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

    Un jour est outlier si :
        units_sold > borne_haute
        ET ce n'est PAS un jour de rupture (is_stockout = False)

    Note : seule la borne haute est utilisée (pas de borne basse). En prévision de
    demande, les valeurs basses représentent une vraie faible demande et ne sont
    PAS des erreurs. Seules les valeurs anormalement HAUTES (erreurs de saisie,
    doublons de commandes) doivent être corrigées. La borne basse génère des faux
    positifs sur les périodes naturellement creuses (ex : valeurs ~3 flaggées alors
    que Q1-1.5*IQR~4) ce qui détériore le MAPE de la pipeline.

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

OUTLIER_ROLLING_WINDOW = 11   # jours pour la médiane glissante centrée de correction
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
import numpy as np
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
        q3 = float(non_stockout.quantile(0.75))
        iqr = q3 - float(non_stockout.quantile(0.25))
        upper_series = pd.Series(q3 + 1.5 * iqr, index=df.index)
    else:
        # ── IQR glissant (DS-2) ───────────────────────────────────────────────
        clean_ref = reference.where(non_stockout_mask)
        q3_roll = clean_ref.rolling(window=iqr_window, min_periods=4).quantile(0.75)
        iqr_roll = q3_roll - clean_ref.rolling(window=iqr_window, min_periods=4).quantile(0.25)
        upper_series = q3_roll + 1.5 * iqr_roll
        # Fallback IQR global pour les NaN en début de série
        q3_global = float(non_stockout.quantile(0.75))
        iqr_global = q3_global - float(non_stockout.quantile(0.25))
        upper_series = upper_series.fillna(q3_global + 1.5 * iqr_global)

    # iqr_lower conservé à 0 pour la compatibilité avec le code existant.
    # La borne basse n'est plus utilisée pour la détection (see docstring).
    df["iqr_lower"] = 0.0
    df["iqr_upper"] = upper_series

    # Flaguer uniquement les outliers HAUTS (jamais les jours de rupture).
    # Les valeurs basses representent une vraie faible demande et ne sont pas corrigees.
    df["is_outlier"] = (
        non_stockout_mask &
        (reference > upper_series)
    )

    # Médiane glissante 7j centrée sur jours propres pour la correction.
    # center=True utilise le contexte avant ET après l'outlier, ce qui donne
    # une correction plus précise qu'une fenêtre backward seule (fix MAPE IQR).
    clean_series = reference.where(~df["is_outlier"] & non_stockout_mask)
    rolling_median = (
        clean_series
        .rolling(window=OUTLIER_ROLLING_WINDOW, min_periods=1, center=True)
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
