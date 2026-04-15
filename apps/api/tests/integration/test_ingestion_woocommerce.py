import pytest
from src.modules.ingestion.connectors.woocommerce import WooCommerceConnector

@pytest.mark.asyncio
async def test_woocommerce_fetch_products():
    """US 9.2 / 10.6 : Teste le parsing des produits WooCommerce."""
    csv_content = (
        "ID,Type,SKU,Name,Published,Stock status,Stock\n"
        "101,simple,SKU-W-1,Robe Noire,1,instock,25\n"
        "102,simple,SKU-W-2,Pantalon Bleu,1,outofstock,0\n"
        "103,variable,,Variante Sans SKU,1,instock,10\n"
    )
    
    connector = WooCommerceConnector()
    products = await connector.fetch_products(csv_content)
    
    # Vérifier que les 2 produits avec SKU sont extraits
    assert len(products) == 2
    assert products[0]["sku"] == "SKU-W-1"
    assert products[0]["current_stock"] == 25
    assert products[1]["sku"] == "SKU-W-2"
    assert products[1]["current_stock"] == 0

@pytest.mark.asyncio
async def test_woocommerce_fetch_sales_history():
    """US 9.2 / 10.6 : Teste le parsing de l'historique de ventes WooCommerce avec aliases."""
    csv_content = (
        "Order ID,Order Date,Status,Item SKU,Item Quantity\n"
        "5001,2025-03-01 10:00:00,completed,SKU-W-1,2\n"
        "5002,2025-03-01 12:00:00,completed,SKU-W-1,3\n"
        "5003,2025-03-02 09:00:00,processing,SKU-W-2,1\n"
        "5004,2025-03-02 11:00:00,cancelled,SKU-W-1,10\n"
    )
    
    connector = WooCommerceConnector()
    sales = await connector.fetch_sales_history(csv_content)
    
    # On attend 2 dates : 
    # - 2025-03-01 pour SKU-W-1 (somme 2+3=5)
    # - 2025-03-02 pour SKU-W-2 (somme 1, car cancelled est ignoré)
    assert len(sales) == 2
    
    # Trier par date pour verification
    sales_sorted = sorted(sales, key=lambda x: str(x["date"]))
    
    assert sales_sorted[0]["sku"] == "SKU-W-1"
    assert sales_sorted[0]["units_sold"] == 5.0
    
    assert sales_sorted[1]["sku"] == "SKU-W-2"
    assert sales_sorted[1]["units_sold"] == 1.0
