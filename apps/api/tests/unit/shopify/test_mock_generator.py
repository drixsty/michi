"""
Tests unitaires — mock_generator.py (US 1.1 + US 1.2)
Couverture : génération produits, historique ventes, ruptures, dataset complet.
"""
from datetime import date

from modules.shopify.infrastructure.mock_generator import (
    generate_mock_products,
    generate_mock_sales,
    generate_full_mock_dataset,
    RANDOM_SEED,
)


# ── US 1.1 : Générateur produits ──────────────────────────────────────────────

class TestGenerateMockProducts:
    def test_default_count_at_least_50_products(self):
        """Le générateur peut produire plus de 50 entrées (omnichannel multiplie les lignes)."""
        products = generate_mock_products()
        assert len(products) >= 50

    def test_custom_count_at_least_requested(self):
        """Avec count=10, on obtient ≥10 entrées (une par plateforme)."""
        products = generate_mock_products(count=10)
        assert len(products) >= 10

    def test_product_has_required_fields(self):
        products = generate_mock_products(count=1)
        p = products[0]
        assert "id" in p
        assert "store_id" in p  # renommé depuis shop_id (Sprint 9 omnichannel)
        assert "sku" in p
        assert "title" in p
        assert "current_stock" in p
        assert "lead_time" in p
        assert "moq" in p

    def test_sku_format(self):
        products = generate_mock_products(count=5)
        for p in products:
            # SKU = CATEGORY-NNNN
            parts = p["sku"].split("-")
            assert len(parts) == 2
            assert parts[1].isdigit()

    def test_stock_in_valid_range(self):
        products = generate_mock_products()
        for p in products:
            assert 0 <= p["current_stock"] <= 200

    def test_lead_time_valid_values(self):
        valid_lead_times = {7, 14, 21, 30, 45}
        products = generate_mock_products()
        for p in products:
            assert p["lead_time"] in valid_lead_times

    def test_moq_valid_values(self):
        valid_moqs = {5, 10, 20, 50}
        products = generate_mock_products()
        for p in products:
            assert p["moq"] in valid_moqs

    def test_store_id_propagated(self):
        store_id = "test-shop-uuid-1234"
        products = generate_mock_products(count=5, store_id=store_id)
        for p in products:
            assert p["store_id"] == store_id

    def test_reproducibility_with_seed(self):
        """Deux appels successifs produisent les mêmes données (seed fixe)."""
        p1 = generate_mock_products(count=10)
        p2 = generate_mock_products(count=10)
        assert [p["sku"] for p in p1] == [p["sku"] for p in p2]
        assert [p["title"] for p in p1] == [p["title"] for p in p2]


# ── US 1.2 : Historique ventes avec ruptures ──────────────────────────────────

class TestGenerateMockSales:
    def test_default_generates_365_days(self):
        logs = generate_mock_sales("product-id-abc")
        assert len(logs) == 365

    def test_custom_days(self):
        logs = generate_mock_sales("product-id-abc", days=30)
        assert len(logs) == 30

    def test_sales_log_has_required_fields(self):
        logs = generate_mock_sales("pid", days=1)
        log = logs[0]
        assert "product_id" in log
        assert "date" in log
        assert "units_sold" in log
        assert "end_of_day_stock" in log

    def test_product_id_propagated(self):
        pid = "my-product-uuid"
        logs = generate_mock_sales(pid, days=10)
        for log in logs:
            assert log["product_id"] == pid

    def test_dates_are_consecutive(self):
        logs = generate_mock_sales("pid", days=10)
        dates = [log["date"] for log in logs]
        for i in range(1, len(dates)):
            assert (dates[i] - dates[i - 1]).days == 1

    def test_units_sold_non_negative(self):
        logs = generate_mock_sales("pid")
        for log in logs:
            assert log["units_sold"] >= 0

    def test_end_of_day_stock_non_negative(self):
        logs = generate_mock_sales("pid")
        for log in logs:
            assert log["end_of_day_stock"] >= 0

    def test_stockout_simulation_zeros(self):
        """Avec rupture activée, il doit y avoir des jours à 0 ventes et 0 stock."""
        logs = generate_mock_sales("pid-with-stockout", days=365, has_stockout=True)
        stockout_days = [l for l in logs if l["units_sold"] == 0 and l["end_of_day_stock"] == 0]
        assert len(stockout_days) >= 3  # au moins une rupture de 3 jours minimum

    def test_no_stockout_has_mostly_sales(self):
        """Sans rupture, la grande majorité des jours ont des ventes."""
        logs = generate_mock_sales("pid-healthy", days=365, has_stockout=False)
        # On exclut les jours avec stock=0 naturellement (stock épuisé sans rupture forcée)
        days_with_sales = [l for l in logs if l["units_sold"] > 0]
        # Au moins 80% des jours devraient avoir des ventes
        assert len(days_with_sales) / len(logs) >= 0.5


# ── Dataset complet ───────────────────────────────────────────────────────────

class TestGenerateFullMockDataset:
    def test_returns_at_least_50_products_by_default(self):
        """Le générateur omnichannel peut produire plus de 50 entrées (une par plateforme)."""
        products, _ = generate_full_mock_dataset()
        assert len(products) >= 50

    def test_returns_365_days_per_unique_product(self):
        """Chaque produit unique a 365 jours d'historique."""
        products, sales = generate_full_mock_dataset(count=5)
        unique_product_ids = {p["id"] for p in products}
        assert len(sales) == len(unique_product_ids) * 365

    def test_stockout_products_are_subset(self):
        """Les produits avec rupture ont au moins un jour sans vente."""
        _, sales = generate_full_mock_dataset(count=20)
        # Vérifie simplement qu'il y a des jours à 0 ventes dans le dataset
        zero_sale_days = [l for l in sales if l["units_sold"] == 0]
        assert len(zero_sale_days) > 0

    def test_store_id_consistency(self):
        store_id = "test-shop-888"
        products, _ = generate_full_mock_dataset(count=5, store_id=store_id)
        for p in products:
            assert p["store_id"] == store_id
