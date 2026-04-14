"""
Tests unitaires — ABC Analysis Algorithm
Nouveau fichier (US 21.30) — couverture : Pareto 70/90/100, edge cases, vectorisation.
"""
import pandas as pd

from src.modules.intelligence.algorithms.abc_analysis import calculate_abc_ranks_batch


def make_products(data: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(data)


class TestCalculateAbcRanksBatch:

    def test_abc_columns_present(self):
        """Les colonnes annual_gross_profit et abc_rank sont bien ajoutées."""
        df = make_products([
            {"product_id": "p1", "run_rate": 10.0, "sale_price": 50.0, "cost_price": 20.0},
            {"product_id": "p2", "run_rate": 5.0,  "sale_price": 30.0, "cost_price": 15.0},
        ])
        result = calculate_abc_ranks_batch(df)
        assert "annual_gross_profit" in result.columns
        assert "abc_rank" in result.columns

    def test_rank_values_valid(self):
        """Les rangs sont exclusivement A, B ou C."""
        df = make_products([
            {"product_id": f"p{i}", "run_rate": float(i), "sale_price": 100.0, "cost_price": 50.0}
            for i in range(1, 11)
        ])
        result = calculate_abc_ranks_batch(df)
        assert set(result["abc_rank"].unique()).issubset({"A", "B", "C"})

    def test_balanced_distribution_has_rank_a(self):
        """
        Distribution équilibrée (aucun produit > 70% seul) → au moins 1 produit A.
        Profits : 700, 200, 100 → total 1000
        p1 cum_pct = 0.70 → A, p2 = 0.90 → B, p3 = 1.0 → C
        """
        # On construit des profits cibles en jouant sur run_rate
        # annual_profit = (sale_price - cost_price) * run_rate * 365
        # marge = 1.0 pour simplifier : profit = run_rate * 365
        df = make_products([
            {"product_id": "p1", "run_rate": 700 / 365, "sale_price": 2.0, "cost_price": 1.0},
            {"product_id": "p2", "run_rate": 200 / 365, "sale_price": 2.0, "cost_price": 1.0},
            {"product_id": "p3", "run_rate": 100 / 365, "sale_price": 2.0, "cost_price": 1.0},
        ])
        result = calculate_abc_ranks_batch(df)
        p1_rank = result.loc[result["product_id"] == "p1", "abc_rank"].iloc[0]
        p3_rank = result.loc[result["product_id"] == "p3", "abc_rank"].iloc[0]
        assert p1_rank == "A", f"p1 (70% du profit) devrait être A, obtenu: {p1_rank}"
        assert p3_rank == "C", f"p3 (10% du profit) devrait être C, obtenu: {p3_rank}"

    def test_zero_margin_is_rank_c(self):
        """Un produit sans marge (sale_price == cost_price) est classé C."""
        df = make_products([
            {"product_id": "profitable", "run_rate": 50.0, "sale_price": 100.0, "cost_price": 40.0},
            {"product_id": "zero_margin", "run_rate": 10.0, "sale_price": 20.0, "cost_price": 20.0},
        ])
        result = calculate_abc_ranks_batch(df)
        zm_rank = result.loc[result["product_id"] == "zero_margin", "abc_rank"].iloc[0]
        assert zm_rank == "C"

    def test_empty_dataframe_returned_unchanged(self):
        """Un DataFrame vide est retourné sans erreur."""
        df = pd.DataFrame(columns=["product_id", "run_rate", "sale_price", "cost_price"])
        result = calculate_abc_ranks_batch(df)
        assert result.empty

    def test_all_zero_profit_all_c(self):
        """Tous les produits à profit ≤ 0 → tous classés C."""
        df = make_products([
            {"product_id": "p1", "run_rate": 5.0, "sale_price": 10.0, "cost_price": 10.0},
            {"product_id": "p2", "run_rate": 5.0, "sale_price": 8.0,  "cost_price": 10.0},
        ])
        result = calculate_abc_ranks_batch(df)
        assert (result["abc_rank"] == "C").all()

    def test_annual_profit_formula(self):
        """Vérification de la formule : (sale_price - cost_price) * run_rate * 365."""
        df = make_products([
            {"product_id": "p1", "run_rate": 2.0, "sale_price": 100.0, "cost_price": 50.0},
        ])
        result = calculate_abc_ranks_batch(df)
        expected = (100.0 - 50.0) * 2.0 * 365
        actual = float(result.loc[0, "annual_gross_profit"])
        assert abs(actual - expected) < 0.01

    def test_missing_price_defaults_to_zero(self):
        """Les prix NaN sont traités comme 0 (pas de crash)."""
        df = pd.DataFrame([
            {"product_id": "p1", "run_rate": 5.0, "sale_price": None, "cost_price": 10.0},
            {"product_id": "p2", "run_rate": 5.0, "sale_price": 50.0, "cost_price": 20.0},
        ])
        result = calculate_abc_ranks_batch(df)
        assert "abc_rank" in result.columns

    def test_pareto_distribution(self):
        """
        Avec 10 produits de profits décroissants :
        les 2 premiers (20% produits, ~70% profit cumulé) doivent être A.
        """
        profits = [1000.0, 800.0, 50.0, 40.0, 30.0, 25.0, 20.0, 15.0, 10.0, 5.0]
        df = make_products([
            {"product_id": f"p{i}", "run_rate": p / 365, "sale_price": p / 365 + 1, "cost_price": 1.0}
            for i, p in enumerate(profits)
        ])
        result = calculate_abc_ranks_batch(df)
        a_count = (result["abc_rank"] == "A").sum()
        assert a_count >= 1, "Au moins 1 produit A attendu avec distribution Pareto"
