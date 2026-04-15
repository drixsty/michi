import pandas as pd
"""
ABC Analysis Algorithm (Sprint 15)
Persona: #2 Data Scientist / ML Engineer

Classifie les produits selon la méthode de Pareto (80/15/5) basée sur la MARGE BRUTE annualisée.
Règle : 
- A : Top 70-80% du profit cumulé (Produits stratégiques)
- B : 15-20% suivants (Produits intermédiaires)
- C : 5-10% restants (Produits à faible impact financier)

Formule de Profit Brut Annuel : (sale_price - cost_price) * (run_rate * 365)
"""
from loguru import logger

def calculate_abc_ranks_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les rangs ABC de manière vectorisée pour un ensemble de produits.
    
    Args:
        df: DataFrame contenant [product_id, run_rate, sale_price, cost_price]
        
    Returns:
        DataFrame avec les colonnes calculées [annual_gross_profit, abc_rank]
    """
    if df.empty:
        return df

    # 1. Calculer le profit brut annuel (Vectorisé)
    # On gère les ventes nulles ou les prix manquants
    df['sale_price'] = df['sale_price'].fillna(0)
    df['cost_price'] = df['cost_price'].fillna(0)
    df['unit_margin'] = df['sale_price'] - df['cost_price']
    
    # 365 jours de projection pour la visibilité financière annuelle
    df['annual_gross_profit'] = df['unit_margin'] * (df['run_rate'] * 365)
    
    # On ne travaille que sur les produits ayant un profit > 0 pour le classement ABC
    # Sinon on les met en C par défaut
    df['abc_rank'] = 'C'
    
    pos_profit_mask = df['annual_gross_profit'] > 0
    if not pos_profit_mask.any():
        logger.warning("[ABC Analysis] Aucun produit avec un profit positif détecté.")
        return df

    # 2. Trier par profit décroissant
    sorted_df = df[pos_profit_mask].sort_values(by='annual_gross_profit', ascending=False).copy()
    
    # 3. Calculer le pourcentage cumulé
    total_profit = sorted_df['annual_gross_profit'].sum()
    sorted_df['cum_profit'] = sorted_df['annual_gross_profit'].cumsum()
    sorted_df['cum_pct'] = sorted_df['cum_profit'] / total_profit
    
    # 4. Assigner les rangs (Standard Pareto 70/90/100)
    def _get_rank(pct: float) -> str:
        if pct <= 0.70: return 'A'
        if pct <= 0.90: return 'B'
        return 'C'
    
    sorted_df['abc_rank'] = sorted_df['cum_pct'].apply(_get_rank)
    
    # 5. Réinjecter les rangs dans le DataFrame original
    df.loc[pos_profit_mask, 'abc_rank'] = sorted_df['abc_rank']
    
    logger.info(f"[ABC Analysis] Rangs calculés : {len(df[df['abc_rank'] == 'A'])} A, {len(df[df['abc_rank'] == 'B'])} B, {len(df[df['abc_rank'] == 'C'])} C")
    
    return df
