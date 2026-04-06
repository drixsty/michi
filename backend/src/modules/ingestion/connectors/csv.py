import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..base import BaseConnector

class CSVConnector(BaseConnector):
    """
    Connecteur Universel CSV pour Michi.
    Permet à n'importe quel marchand d'importer ses données.
    """

    async def fetch_products(self, csv_content: str, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Ingère les produits depuis un contenu CSV.
        mapping: { "sku": "col_name_in_csv", "title": "...", "stock": "..." }
        """
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Application du mapping
        products = []
        for _, row in df.iterrows():
            product = {
                "sku": str(row[mapping["sku"]]),
                "title": str(row.get(mapping.get("title", "title"), "Produit CSV")),
                "current_stock": int(row.get(mapping.get("stock", "stock"), 0))
            }
            products.append(product)
            
        return products

    async def fetch_sales_history(self, csv_content: str, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Ingère l'historique des ventes depuis un CSV.
        mapping: { "sku": "...", "date": "...", "units_sold": "..." }
        """
        df = pd.read_csv(io.StringIO(csv_content))
        
        # Conversion du format de date (Agnostic - Pandas gère bien les formats communs)
        df[mapping["date"]] = pd.to_datetime(df[mapping["date"]])
        
        sales = []
        for _, row in df.iterrows():
            sale = {
                "sku": str(row[mapping["sku"]]),
                "date": row[mapping["date"]].date(),
                "units_sold": float(row[mapping["units_sold"]]),
                "end_of_day_stock": int(row.get(mapping.get("stock", "stock"), 0))
            }
            sales.append(sale)
            
        return sales
