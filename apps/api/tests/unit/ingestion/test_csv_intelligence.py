import pytest
import io
import pandas as pd
from datetime import date
from modules.ingestion.connectors.csv import CSVConnector

@pytest.mark.asyncio
async def test_csv_ingestion_intelligence():
    connector = CSVConnector()
    
    # --- 1. Test Intelligence Inventaire (Déduplication & Nettoyage) ---
    csv_inventory = """sku;title;stock
PROD-01;Produit 1;10
prod-01;Produit 1 bis;15
  prod-02  ;Produit 2;5
"""
    mapping = {"sku": "sku", "title": "title", "stock": "stock"}
    
    # Note: On force le séparateur ; pour ce test si nécessaire, 
    # mais pd.read_csv est généralement assez malin. 
    # Ici on utilise le défaut , pour être sûr.
    csv_inventory = csv_inventory.replace(";", ",")
    
    products = await connector.fetch_products(csv_inventory, mapping)
    
    # Résultats attendus :
    # - PROD-01 et prod-01 fusionnés en PROD-01 (Dernière valeur 15 gagne)
    # - prod-02 devient PROD-02 (Trim + Uppercase)
    assert len(products) == 2
    
    prod_01 = next(p for p in products if p["sku"] == "PROD-01")
    assert prod_01["current_stock"] == 15
    
    prod_02 = next(p for p in products if p["sku"] == "PROD-02")
    assert prod_02["sku"] == "PROD-02"

    # --- 1b. Test Fuzzy Matching ---
    existing = ["IPHONE-13-BLUE", "MACBOOK-PRO"]
    csv_fuzzy = """sku,title,stock
iphone13blue,iPhone 13 Bleu,5
"""
    products_fuzzy = await connector.fetch_products(csv_fuzzy, mapping, existing_skus=existing)
    
    # Doit rapprocher 'iphone13blue' vers 'IPHONE-13-BLUE'
    assert len(products_fuzzy) == 1
    assert products_fuzzy[0]["sku"] == "IPHONE-13-BLUE"
    # --- 2. Test Intelligence Ventes (Agrégation par date) ---
    csv_sales = """sku,date,units,stock
PROD-01,01/04/2026,5,10
PROD-01,01/04/2026,3,8
PROD-01,02/04/2026,10,20
"""
    sales_mapping = {"sku": "sku", "date": "date", "units_sold": "units", "stock": "stock"}
    
    sales = await connector.fetch_sales_history(csv_sales, sales_mapping)
    
    # Doit contenir au moins les deux jours
    assert len(sales) >= 2
    
    sale_01 = next(s for s in sales if s["date"] == date(2026, 4, 1))
    assert sale_01["units_sold"] == 8.0
    assert sale_01["end_of_day_stock"] == 8 # Dernier stock connu
    
    sale_02 = next(s for s in sales if s["date"] == date(2026, 4, 2))
    assert sale_02["units_sold"] == 10.0

    # --- 3. Test Interpolation (Jours manquants) ---
    print("DEBUG: Starting Interpolation test...")
    csv_gap = """sku,date,units,stock
GAP-01,01/04/2026,10,100
GAP-01,02/04/2026,5,95
GAP-01,04/04/2026,8,87
"""
    gap_mapping = {"sku": "sku", "date": "date", "units_sold": "units", "stock": "stock"}
    sales_gap = await connector.fetch_sales_history(csv_gap, gap_mapping)
    
    assert len(sales_gap) == 4
    
    # Vérifier le jour interpolé (03/04)
    sale_03 = next(s for s in sales_gap if s["date"] == date(2026, 4, 3))
    assert sale_03["units_sold"] == 0.0
    assert sale_03["is_interpolated"] is True
    assert sale_03["end_of_day_stock"] == 95 # Report du dernier stock connu
    
    # --- 4. Test Excel Support ---
    # On va lire le fichier généré par le script
    import os
    excel_path = "apps/api/tests/data/michi_test_full.xlsx"
    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            excel_content = f.read()
        
        excel_mapping = {"sku": "Reference", "date": "Date Vente", "units_sold": "Ventes", "stock": "Stock"}
        sales_excel = await connector.fetch_sales_history(excel_content, excel_mapping, is_excel=True)
        
        assert len(sales_excel) > 0
        assert sales_excel[0]["sku"] == "PROD-EXCEL"
        assert "is_interpolated" in sales_excel[0]

@pytest.mark.asyncio
async def test_csv_numeric_flexibility():
    connector = CSVConnector()
    csv_data = """sku,stock
PROD-FR,"10,5"
PROD-US,20.7
"""
    mapping = {"sku": "sku", "stock": "stock"}
    products = await connector.fetch_products(csv_data, mapping)
    
    prod_fr = next(p for p in products if p["sku"] == "PROD-FR")
    assert prod_fr["current_stock"] == 10 # 10.5 converti en int -> 10
    
    prod_us = next(p for p in products if p["sku"] == "PROD-US")
    assert prod_us["current_stock"] == 20
