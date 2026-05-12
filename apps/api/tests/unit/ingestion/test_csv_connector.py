import pytest
from modules.ingestion.connectors.csv import CSVConnector
import io
import pandas as pd

@pytest.mark.asyncio
async def test_csv_discover_schema_clean_file():
    connector = CSVConnector()
    csv_content = """sku,designation,quantite_stock
PROD-001,Produit 1,100
PROD-002,Produit 2,50"""
    
    analysis = await connector.discover_schema(csv_content)
    
    assert "sku" in analysis["columns"]
    assert "designation" in analysis["columns"]
    assert analysis["suggested_mapping"]["sku"] == "sku"
    assert analysis["suggested_mapping"]["title"] == "designation"
    assert analysis["suggested_mapping"]["stock"] == "quantite_stock"
    assert len(analysis["sample_data"]) == 2

@pytest.mark.asyncio
async def test_csv_discover_schema_with_synonyms():
    connector = CSVConnector()
    # Utilisation de synonymes complexes
    csv_content = """Ref_Produit,Label,Inventory_Level
REF123,Mon Produit,10"""
    
    analysis = await connector.discover_schema(csv_content)
    
    assert analysis["suggested_mapping"]["sku"] == "Ref_Produit"
    assert analysis["suggested_mapping"]["title"] == "Label"
    assert analysis["suggested_mapping"]["stock"] == "Inventory_Level"

@pytest.mark.asyncio
async def test_csv_discover_anomalies():
    connector = CSVConnector()
    csv_content = """sku,stock,units_sold
PROD-001,10,5
PROD-002,-5,10
PROD-003,20,-2"""
    
    analysis = await connector.discover_schema(csv_content)
    anomalies = analysis["anomalies"]
    
    # Ligne 1 (index 1 dans df car index 0 est valide)
    # Attendu: anomalies pour PROD-002 (stock -5) et PROD-003 (units_sold -2)
    assert len(anomalies) == 2
    
    # Vérification de l'erreur sur PROD-002
    prod2_error = next(a for a in anomalies if a["row"] == 1)
    assert prod2_error["errors"]["stock"] == "NEGATIVE_VALUE"
    
    # Vérification de l'erreur sur PROD-003
    prod3_error = next(a for a in anomalies if a["row"] == 2)
    assert prod3_error["errors"]["units_sold"] == "NEGATIVE_VALUE"

@pytest.mark.asyncio
async def test_csv_fetch_products_with_mapping():
    connector = CSVConnector()
    csv_content = """Ref,Nom,Qte
P1,T-Shirt,10"""
    mapping = {"sku": "Ref", "title": "Nom", "stock": "Qte"}
    
    products = await connector.fetch_products(csv_content, mapping)
    
    assert len(products) == 1
    assert products[0]["sku"] == "P1"
    assert products[0]["title"] == "T-Shirt"
    assert products[0]["current_stock"] == 10
