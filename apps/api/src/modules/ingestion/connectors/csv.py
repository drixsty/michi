import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from ..domain.base import BaseConnector

class CSVConnector(BaseConnector):
    """
    Connecteur Universel CSV/Excel pour Michi.
    """

    async def fetch_products(self, content: Any, mapping: Dict[str, str], existing_skus: List[str] = None, is_excel: bool = False) -> List[Dict[str, Any]]:
        """
        Ingère les produits avec intelligence IA (Déduplication & Fuzzy Matching).
        """
        import difflib
        if is_excel:
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.StringIO(content) if isinstance(content, str) else io.BytesIO(content))
            
        df.columns = [c.strip() for c in df.columns]
        
        if "sku" not in mapping or mapping["sku"] not in df.columns:
            return []
            
        unique_products = {}
        
        for _, row in df.iterrows():
            raw_sku = str(row[mapping["sku"]]).strip().upper()
            if not raw_sku or raw_sku == "NAN":
                continue
            
            # IA : Fuzzy matching avec l'existant
            target_sku = raw_sku
            if existing_skus:
                if raw_sku not in existing_skus:
                    matches = difflib.get_close_matches(raw_sku, existing_skus, n=1, cutoff=0.85)
                    if matches:
                        logger.info(f"[Ingestion IA] Rapprochement flou: '{raw_sku}' -> '{matches[0]}'")
                        target_sku = matches[0]
                
            title = str(row.get(mapping.get("title", "title"), "Produit CSV")).strip()
            
            raw_stock = str(row.get(mapping.get("stock", "stock"), 0)).replace(",", ".")
            try:
                stock = int(float(raw_stock))
            except:
                stock = 0
                
            unique_products[target_sku] = {
                "sku": target_sku,
                "title": title,
                "current_stock": max(0, stock)
            }
            
        return list(unique_products.values())

    async def fetch_sales_history(self, content: Any, mapping: Dict[str, str], is_excel: bool = False) -> List[Dict[str, Any]]:
        """
        Ingère l'historique avec agrégation, interpolation et détection d'anomalies.
        """
        if is_excel:
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.StringIO(content) if isinstance(content, str) else io.BytesIO(content))
            
        df.columns = [c.strip() for c in df.columns]
        
        if mapping["date"] not in df.columns or mapping["units_sold"] not in df.columns:
            return []

        df[mapping["date"]] = pd.to_datetime(df[mapping["date"]], dayfirst=True, errors='coerce', format='mixed')
        df = df.dropna(subset=[mapping["date"]])
        
        sales_map = {} 
        if df.empty: return []
        
        min_date = df[mapping["date"]].min()
        max_date = df[mapping["date"]].max()
        
        for _, row in df.iterrows():
            sku = str(row[mapping["sku"]]).strip().upper()
            if not sku or sku == "NAN": continue
            dt = row[mapping["date"]].date()
            
            raw_units = str(row[mapping["units_sold"]]).replace(",", ".")
            try:
                units = max(0.0, float(raw_units))
            except:
                units = 0.0
            
            raw_stock = str(row.get(mapping.get("stock", "stock"), 0)).replace(",", ".")
            try:
                stock = max(0, int(float(raw_stock)))
            except:
                stock = 0

            key = (dt, sku)
            if key in sales_map:
                sales_map[key]["units_sold"] += units
                sales_map[key]["end_of_day_stock"] = stock
            else:
                sales_map[key] = {"sku": sku, "date": dt, "units_sold": units, "end_of_day_stock": stock}
        
        # Interpolation
        from datetime import timedelta
        final_sales = []
        all_skus = [str(s).strip().upper() for s in df[mapping["sku"]].unique() if pd.notna(s)]
        
        for sku_upper in all_skus:
            sku_sales_data = [s for s in sales_map.values() if s["sku"] == sku_upper]
            if not sku_sales_data: continue
            
            units_vals = [s["units_sold"] for s in sku_sales_data]
            avg = sum(units_vals) / len(units_vals)
            std = (sum((x - avg) ** 2 for x in units_vals) / len(units_vals)) ** 0.5
            
            curr_dt = min_date.date()
            end_dt = max_date.date()
            last_known_stock = 0
            
            while curr_dt <= end_dt:
                key = (curr_dt, sku_upper)
                if key in sales_map:
                    sale = sales_map[key]
                    last_known_stock = sale["end_of_day_stock"]
                    sale["is_anomaly"] = False
                    if std > 0.001:
                        z = abs(sale["units_sold"] - avg) / std
                        if z > 3: sale["is_anomaly"] = True
                    final_sales.append(sale)
                else:
                    final_sales.append({
                        "sku": sku_upper, "date": curr_dt, "units_sold": 0.0,
                        "end_of_day_stock": last_known_stock, "is_anomaly": False, "is_interpolated": True
                    })
                curr_dt += timedelta(days=1)

        return final_sales

    async def discover_schema(self, content: Any, is_excel: bool = False) -> Dict[str, Any]:
        """
        Analyse le schéma pour suggestion de mapping et impact.
        """
        if is_excel:
            df = pd.read_excel(io.BytesIO(content), nrows=100)
        else:
            try:
                df = pd.read_csv(io.StringIO(content) if isinstance(content, str) else io.BytesIO(content), nrows=100)
            except:
                return {"error": "Format invalide"}
                
        columns = [c.strip() for c in df.columns]
        df.columns = columns
        
        synonyms = {
            "sku": ["sku", "reference", "ref", "code", "id", "article", "ean", "upc"],
            "title": ["title", "name", "nom", "designation", "label", "produit", "product"],
            "stock": ["stock", "quantity", "quantite", "inventory", "available", "disponible", "on_hand"],
            "date": ["date", "day", "jour", "timestamp", "period", "periode", "sold_at"],
            "units_sold": ["units_sold", "sold", "quantity_sold", "ventes", "vendu", "qty", "amount"]
        }

        suggested_mapping = {}
        column_types = {}

        for col in columns:
            col_lower = col.lower().strip()
            mapped = False
            for target, words in synonyms.items():
                if any(word in col_lower for word in words):
                    if target not in suggested_mapping:
                        suggested_mapping[target] = col
                        mapped = True
                        break
            
            if not mapped:
                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                if sample is not None:
                    try:
                        if isinstance(sample, str) and len(sample) > 6:
                            pd.to_datetime(sample)
                            if "date" not in suggested_mapping:
                                suggested_mapping["date"] = col
                    except: pass
            
            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = "number"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                column_types[col] = "date"
            else:
                column_types[col] = "string"

        anomalies = []
        for i, row in df.iterrows():
            row_anomalies = {}
            for target, col in suggested_mapping.items():
                val = row.get(col)
                if pd.isna(val):
                    row_anomalies[col] = "MISSING"
                elif target in ["stock", "units_sold"] and pd.api.types.is_numeric_dtype(df[col]):
                    if val < 0:
                        row_anomalies[col] = "NEGATIVE_VALUE"
            if row_anomalies:
                anomalies.append({"row": i, "errors": row_anomalies})

        total_rows = len(df)
        unique_skus = df[suggested_mapping["sku"]].nunique() if "sku" in suggested_mapping else 0

        return {
            "columns": columns,
            "column_types": column_types,
            "suggested_mapping": suggested_mapping,
            "sample_data": df.head(10).fillna("").to_dict(orient="records"),
            "anomalies": anomalies,
            "impact": {
                "total_rows": total_rows,
                "unique_skus": unique_skus,
                "is_excel": is_excel
            }
        }
