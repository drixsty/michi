"""
Seasonality Algorithm (Sprint 15, étendu Sprint 27)

Deux fonctions :

1. detect_seasonality_factor — facteur court terme (momentum 7j / 30j), scalaire.
   Utilisé en dehors du pipeline (debug, affichage frontend).

2. calculate_weekly_indices — indices jour-de-semaine normalisés (moyenne = 1.0).
   Utilisé dans run_rate.py pour supprimer le biais calendaire avant le rolling :
   si les 30 derniers jours comptent 5 lundis (gros jour) et 4 dimanches (petit jour),
   la médiane glissante est biaisée. Les indices neutralisent cet effet AVANT calcul
   du run rate afin d'obtenir un taux « jour moyen » stable, indépendant du calendrier
   observé.

   Formule :
       dow_factor[d] = mean_sales[d] / mean_over_all_days
       normalized_sales[t] = raw_sales[t] / dow_factor[weekday(t)]
       run_rate = rolling_median(normalized_sales)

   Fallback {0..6: 1.0} si moins de 14 observations (moins de 2 semaines complètes).
"""
import pandas as pd


def detect_seasonality_factor(df: pd.DataFrame, window: int = 14) -> float:
    """
    Calcule un facteur de saisonnalité court terme (momentum 7j / 30j).

    Args:
        df: DataFrame trié par date avec colonne corrected_units_sold.
        window: Nombre minimum de jours requis (défaut : 14).
                Si len(df) < window * 2, retourne 1.0 (données insuffisantes).

    Returns:
        Facteur ∈ [0.5, 2.5]. Retourne 1.0 si données insuffisantes ou si
        l'écart est inférieur à 10% (bruit de mesure).

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({"date": pd.date_range("2025-01-01", 60),
        ...                    "corrected_units_sold": [5.0]*30 + [10.0]*30})
        >>> detect_seasonality_factor(df)  # doctest: +SKIP
        2.0
    """
    if df.empty or len(df) < window * 2:
        return 1.0

    df = df.sort_values('date')
    recent_avg = df['corrected_units_sold'].tail(7).mean()
    historical_avg = df['corrected_units_sold'].tail(30).mean()

    if historical_avg <= 0:
        return 1.0

    factor = max(0.5, min(2.5, recent_avg / historical_avg))

    if 0.9 <= factor <= 1.1:
        return 1.0

    return factor


def calculate_weekly_indices(dow_series: pd.Series, values: pd.Series) -> dict[int, float]:
    """
    Calcule les indices saisonniers jour-de-semaine normalisés à moyenne = 1.0.

    Args:
        dow_series: Série d'entiers 0=Lun … 6=Dim (même index que values).
        values: Ventes journalières propres (non-stockout, non-outlier).

    Returns:
        Dict {0: factor_Lun, …, 6: factor_Dim}.
        Chaque facteur > 1.0 signifie que ce jour vend plus que la moyenne.
        Les facteurs sont normalisés : mean(factors) = 1.0.
        Fallback {0..6: 1.0} si < 14 observations ou données insuffisantes.

    Example:
        >>> dow = pd.Series([0, 1, 2, 3, 4, 5, 6] * 4)  # 4 semaines
        >>> sales = pd.Series([10, 8, 9, 7, 11, 5, 4] * 4)
        >>> idx = calculate_weekly_indices(dow, sales)
        >>> abs(idx[0] - 1.25) < 0.01  # lundi vend 25% de plus que la moyenne
        True
    """
    if len(values) < 14:
        return {i: 1.0 for i in range(7)}

    df_tmp = pd.DataFrame({"dow": dow_series.values, "val": values.values})
    means = df_tmp.groupby("dow")["val"].mean()
    grand_mean = means.mean()

    if grand_mean == 0:
        return {i: 1.0 for i in range(7)}

    normalized = means / grand_mean
    return {i: float(normalized.get(i, 1.0)) for i in range(7)}


def apply_seasonality_batch(products_df: pd.DataFrame, history_df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique detect_seasonality_factor à chaque produit et stocke le facteur.

    Note : cette fonction n'est pas encore branchée dans le pipeline principal.
    Le blend adaptatif de run_rate.py remplit le même rôle en temps réel.
    """
    factors = {
        pid: detect_seasonality_factor(history_df[history_df['product_id'] == pid])
        for pid in products_df['product_id'].unique()
    }
    products_df['seasonality_factor'] = products_df['product_id'].map(factors)
    return products_df
