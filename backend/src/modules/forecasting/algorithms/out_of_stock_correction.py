"""
Out-of-Stock Correction Algorithm — US 2.1

Objectif :
    Corriger les jours de rupture de stock (end_of_day_stock = 0) en estimant
    la demande théorique non satisfaite via une moyenne mobile glissante de 14 jours
    calculée sur les jours non-rupture précédents.

Formule :
    Pour chaque jour j où end_of_day_stock[j] == 0 :
        theoretical_units_sold[j] = mean(units_sold[k] pour k dans [j-14..j-1] où stock[k] > 0)

    Si aucun jour non-rupture n'existe dans la fenêtre de 14 jours :
        theoretical_units_sold[j] = median(units_sold sur toute la série non-rupture)

Hypothèses :
    - La demande est stable sur 14 jours (distribution normale)
    - Les jours de pic (Black Friday, soldes) ne sont PAS exclus car ils font
      partie de la demande réelle
    - Un stock = 0 en fin de journée indique une rupture (pas une vente nulle)

Performance :
    O(n) avec vectorisation Pandas — interdit les boucles for sur les lignes.
"""
import pandas as pd
import numpy as np
from typing import Optional

ROLLING_WINDOW = 14   # jours de fenêtre glissante


def correct_out_of_stock(df: pd.DataFrame) -> pd.DataFrame:
    """
    Corrige les ventes des jours de rupture pour un seul produit.

    Args:
        df: DataFrame avec colonnes [date, units_sold, end_of_day_stock].
            Doit être trié par date croissante.
            Doit contenir les données d'UN seul produit.

    Returns:
        DataFrame original enrichi avec :
        - ``is_stockout`` (bool) : True si le jour est une rupture
        - ``theoretical_units_sold`` (float) : ventes corrigées

    Raises:
        ValueError: Si les colonnes requises sont manquantes.

    Example:
        >>> df = pd.DataFrame({
        ...     "date": pd.date_range("2025-01-01", periods=20),
        ...     "units_sold": [5.0]*15 + [0.0]*5,
        ...     "end_of_day_stock": [100]*15 + [0]*5,
        ... })
        >>> result = correct_out_of_stock(df)
        >>> result["theoretical_units_sold"].iloc[-1]
        5.0
    """
    required = {"date", "units_sold", "end_of_day_stock"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    df = df.sort_values("date").copy()

    # Identifier les jours de rupture
    df["is_stockout"] = df["end_of_day_stock"] == 0

    # Copier les ventes brutes
    df["theoretical_units_sold"] = df["units_sold"].copy()

    # Ventes non-rupture pour la fenêtre glissante
    non_stockout_sales = df["units_sold"].where(~df["is_stockout"])

    # Moyenne mobile 14j (min_periods=1 pour éviter les NaN en début de série)
    rolling_mean = (
        non_stockout_sales
        .rolling(window=ROLLING_WINDOW, min_periods=1)
        .mean()
    )

    # Fallback : médiane globale des jours non-rupture
    global_median = df.loc[~df["is_stockout"], "units_sold"].median()
    if pd.isna(global_median):
        global_median = 0.0

    # Appliquer la correction sur les jours de rupture
    stockout_mask = df["is_stockout"]
    correction = rolling_mean.where(stockout_mask).fillna(global_median)
    df.loc[stockout_mask, "theoretical_units_sold"] = correction[stockout_mask]

    # Garantir non-négatif
    df["theoretical_units_sold"] = df["theoretical_units_sold"].clip(lower=0.0)

    return df


def correct_out_of_stock_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique la correction OOS sur un DataFrame multi-produits.

    Args:
        df: DataFrame avec colonnes [product_id, date, units_sold, end_of_day_stock].

    Returns:
        DataFrame enrichi avec ``is_stockout`` et ``theoretical_units_sold``.

    Notes:
        Utilise groupby + apply pour traiter chaque produit indépendamment.
        Interdit les boucles for sur les lignes (O(n) vectorisé).
    """
    required = {"product_id", "date", "units_sold", "end_of_day_stock"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    result = (
        df.groupby("product_id", group_keys=False)
        .apply(correct_out_of_stock)
        .reset_index(drop=True)
    )
    return result
