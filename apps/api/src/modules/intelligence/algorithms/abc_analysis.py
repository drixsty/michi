"""
ABC Analysis Algorithm (Sprint 15, corrigé Sprint 26-27)

Classifie les produits selon la méthode de Pareto basée sur la MARGE BRUTE annualisée.

Seuils Pareto corrigés (Sprint 26) :
    A : 0-80% du profit cumulé  (standard industriel 80/15/5)
    B : 80-95%
    C : 95-100%

Correction Sprint 27 — robustesse saisonnière :
    Problème : annual_gross_profit = unit_margin × run_rate × 365 utilise le run_rate
    du moment (médiane 30j glissante). En pic saisonnier (ex : Noël), run_rate est 3×
    la normale → produit classé A. Hors-saison, même produit classé C. Résultat :
    le référentiel ABC se recalcule différemment selon la saison, rendant les décisions
    d'achat instables et les comparaisons inter-périodes impossibles.

    Fix : si la colonne `annual_units_sold` est présente (ventes réelles sur 365j,
    passées par forecasting_service), elle est utilisée à la place de run_rate × 365.
    Cette colonne est calculée dans forecasting_service.py comme :
        sum(corrected_units_sold) / observed_days × 365  (si observed_days >= 90)
    Fallback run_rate × 365 si annual_units_sold est NaN (historique < 90 jours).

Formule profit brut annuel :
    annual_gross_profit = unit_margin × annual_units_sold   (si annual_units_sold disponible)
    annual_gross_profit = unit_margin × run_rate × 365      (fallback)
"""
import pandas as pd
from loguru import logger

_ABC_A_THRESHOLD = 0.80
_ABC_B_THRESHOLD = 0.95


def calculate_abc_ranks_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les rangs ABC de manière vectorisée pour un ensemble de produits.

    Args:
        df: DataFrame contenant [product_id, run_rate, sale_price, cost_price].
            Colonne optionnelle : annual_units_sold (ventes réelles annualisées).
            Si présente et non-NaN, utilisée à la place de run_rate × 365
            pour neutraliser les biais saisonniers.

    Returns:
        DataFrame avec [annual_gross_profit, abc_rank].
        Produits à profit <= 0 : classe 'C' par défaut.
        Produits à marge négative : classe 'C' (distinct financièrement mais pas en rank).
    """
    if df.empty:
        return df

    df['sale_price'] = df['sale_price'].fillna(0)
    df['cost_price'] = df['cost_price'].fillna(0)
    df['unit_margin'] = df['sale_price'] - df['cost_price']

    # Annualisation robuste : préférer les ventes réelles observées au run_rate snapshot
    if 'annual_units_sold' in df.columns:
        annual_units = df['annual_units_sold'].fillna(df['run_rate'] * 365)
    else:
        annual_units = df['run_rate'] * 365
    df['annual_gross_profit'] = df['unit_margin'] * annual_units

    df['abc_rank'] = 'C'

    pos_profit_mask = df['annual_gross_profit'] > 0
    if not pos_profit_mask.any():
        logger.warning("[ABC Analysis] Aucun produit avec un profit positif détecté.")
        return df

    sorted_df = df[pos_profit_mask].sort_values(by='annual_gross_profit', ascending=False).copy()

    total_profit = sorted_df['annual_gross_profit'].sum()
    sorted_df['cum_profit'] = sorted_df['annual_gross_profit'].cumsum()
    sorted_df['cum_pct'] = sorted_df['cum_profit'] / total_profit

    def _get_rank(pct: float) -> str:
        if pct <= _ABC_A_THRESHOLD:
            return 'A'
        if pct <= _ABC_B_THRESHOLD:
            return 'B'
        return 'C'

    sorted_df['abc_rank'] = sorted_df['cum_pct'].apply(_get_rank)
    df.loc[pos_profit_mask, 'abc_rank'] = sorted_df['abc_rank']

    logger.info(
        f"[ABC Analysis] Rangs calculés : "
        f"{len(df[df['abc_rank'] == 'A'])} A, "
        f"{len(df[df['abc_rank'] == 'B'])} B, "
        f"{len(df[df['abc_rank'] == 'C'])} C"
    )
    return df
