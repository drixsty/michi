import pandas as pd
import io
from typing import List, Dict, Any, Optional
from datetime import timedelta
from loguru import logger
from ..domain.base import BaseConnector
from ..domain.schemas import IngestedProduct, IngestedSale

_MAX_FILE_BYTES = 50 * 1024 * 1024   # 50 MB
_MAX_ROWS = 100_000                   # 100 k lignes


def _enforce_limits(content: Any) -> None:
    """Lève ValueError si le contenu dépasse les limites de sécurité."""
    size = len(content) if isinstance(content, (bytes, str)) else 0
    if size > _MAX_FILE_BYTES:
        raise ValueError(
            f"Fichier trop volumineux ({size // (1024 * 1024)} MB). "
            f"Limite : {_MAX_FILE_BYTES // (1024 * 1024)} MB."
        )


def _read_df(content: Any, is_excel: bool, nrows: Optional[int] = None) -> pd.DataFrame:
    """Lit le contenu CSV ou Excel en DataFrame."""
    if is_excel:
        buf = io.BytesIO(content) if isinstance(content, bytes) else io.BytesIO(content.encode())
        return pd.read_excel(buf, nrows=nrows)
    buf: Any = io.StringIO(content) if isinstance(content, str) else io.BytesIO(content)
    return pd.read_csv(buf, nrows=nrows)


class CSVConnector(BaseConnector):
    """
    Connecteur Universel CSV/Excel pour Michi.
    Les params spécifiques (content, mapping, is_excel…) transitent via **kwargs
    conformément au contrat BaseConnector.
    """

    async def validate_connection(self, credentials: Dict[str, Any]) -> bool:
        return True

    async def fetch_all_data(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "CSVConnector: use fetch_products / fetch_sales_history with content= kwarg"
        )

    async def fetch_products(
        self,
        shop_id: str,  # noqa: ARG002 — required by BaseConnector; CSV uses content= kwarg
        credentials: Optional[Dict[str, Any]] = None,  # noqa: ARG002
        **kwargs: Any,
    ) -> List[IngestedProduct]:
        """
        Ingère les produits.
        kwargs attendus : content, mapping, existing_skus=None, is_excel=False
        """
        import difflib

        content = kwargs.get("content")
        mapping: Optional[Dict[str, str]] = kwargs.get("mapping")
        existing_skus: Optional[List[str]] = kwargs.get("existing_skus")
        is_excel: bool = kwargs.get("is_excel", False)

        if content is None:
            content = shop_id
        if mapping is None and isinstance(credentials, dict):
            mapping = credentials

        _enforce_limits(content)
        df = _read_df(content, is_excel)

        if len(df) > _MAX_ROWS:
            raise ValueError(
                f"Trop de lignes ({len(df):,}). Limite : {_MAX_ROWS:,} lignes par import."
            )

        df.columns = [c.strip() for c in df.columns]

        if not mapping or "sku" not in mapping or mapping["sku"] not in df.columns:
            return []

        unique_products: Dict[str, Dict[str, Any]] = {}

        for _, row in df.iterrows():
            raw_sku = str(row[mapping["sku"]]).strip().upper()
            if not raw_sku or raw_sku == "NAN":
                continue

            target_sku = raw_sku
            if existing_skus and raw_sku not in existing_skus:
                matches = difflib.get_close_matches(raw_sku, existing_skus, n=1, cutoff=0.85)
                if matches:
                    logger.info(f"[Ingestion IA] Fuzzy match: '{raw_sku}' → '{matches[0]}'")
                    target_sku = matches[0]

            title = str(row.get(mapping.get("title", "title"), "Produit CSV")).strip()

            raw_stock = str(row.get(mapping.get("stock", "stock"), 0)).replace(",", ".")
            try:
                stock = int(float(raw_stock))
            except (ValueError, TypeError):
                stock = 0

            unique_products[target_sku] = {
                "sku": target_sku,
                "title": title,
                "current_stock": max(0, stock),
            }

        return [IngestedProduct(**p) for p in unique_products.values()]

    async def fetch_sales_history(
        self,
        product_sku: str,  # noqa: ARG002 — required by BaseConnector; CSV uses content= kwarg
        shop_id: str,  # noqa: ARG002
        days: int = 365,  # noqa: ARG002
        credentials: Optional[Dict[str, Any]] = None,  # noqa: ARG002
        **kwargs: Any,
    ) -> List[IngestedSale]:
        """
        Ingère l'historique avec agrégation, interpolation et détection d'anomalies.
        kwargs attendus : content, mapping, is_excel=False
        """
        content = kwargs.get("content")
        mapping: Optional[Dict[str, str]] = kwargs.get("mapping")
        is_excel: bool = kwargs.get("is_excel", False)

        if content is None:
            content = product_sku
        if mapping is None and isinstance(shop_id, dict):
            mapping = shop_id
        if not is_excel and isinstance(days, bool):
            is_excel = days

        _enforce_limits(content)
        df = _read_df(content, is_excel)

        if len(df) > _MAX_ROWS:
            raise ValueError(
                f"Trop de lignes ({len(df):,}). Limite : {_MAX_ROWS:,} lignes par import."
            )

        df.columns = [c.strip() for c in df.columns]

        if not mapping or "date" not in mapping or "units_sold" not in mapping:
            return []
        if mapping["date"] not in df.columns or mapping["units_sold"] not in df.columns:
            return []

        df[mapping["date"]] = pd.to_datetime(
            df[mapping["date"]], dayfirst=True, errors="coerce", format="mixed"
        )
        df = df.dropna(subset=[mapping["date"]])

        if df.empty:
            return []

        sales_map: Dict[tuple, Dict[str, Any]] = {}
        min_date = df[mapping["date"]].min()
        max_date = df[mapping["date"]].max()

        for _, row in df.iterrows():
            sku = str(row[mapping["sku"]]).strip().upper()
            if not sku or sku == "NAN":
                continue
            dt = row[mapping["date"]].date()

            raw_units = str(row[mapping["units_sold"]]).replace(",", ".")
            try:
                units = max(0.0, float(raw_units))
            except (ValueError, TypeError):
                units = 0.0

            raw_stock = str(row.get(mapping.get("stock", "stock"), 0)).replace(",", ".")
            try:
                stock = max(0, int(float(raw_stock)))
            except (ValueError, TypeError):
                stock = 0

            key = (dt, sku)
            if key in sales_map:
                sales_map[key]["units_sold"] += units
                sales_map[key]["end_of_day_stock"] = stock
            else:
                sales_map[key] = {
                    "sku": sku,
                    "date": dt,
                    "units_sold": units,
                    "end_of_day_stock": stock,
                }

        final_sales: List[Dict[str, Any]] = []
        all_skus = [
            str(s).strip().upper()
            for s in df[mapping["sku"]].unique()
            if pd.notna(s)
        ]

        for sku_upper in all_skus:
            sku_sales_data = [s for s in sales_map.values() if s["sku"] == sku_upper]
            if not sku_sales_data:
                continue

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
                        if z > 3:
                            sale["is_anomaly"] = True
                    final_sales.append(sale)
                else:
                    final_sales.append({
                        "sku": sku_upper,
                        "date": curr_dt,
                        "units_sold": 0.0,
                        "end_of_day_stock": last_known_stock,
                        "is_anomaly": False,
                        "is_interpolated": True,
                    })
                curr_dt += timedelta(days=1)

        return [IngestedSale(**s) for s in final_sales]

    async def discover_schema(
        self, content: Any, is_excel: bool = False
    ) -> Dict[str, Any]:
        """
        Analyse le schéma pour suggestion de mapping et impact.
        """
        _enforce_limits(content)

        try:
            df = _read_df(content, is_excel, nrows=100)
        except Exception as exc:
            logger.warning(f"[CSVConnector] discover_schema parse error: {exc}")
            return {"error": "Format invalide"}

        columns = [c.strip() for c in df.columns]
        df.columns = columns

        synonyms = {
            "sku": ["sku", "reference", "ref", "code", "id", "article", "ean", "upc"],
            "title": ["title", "name", "nom", "designation", "label", "produit", "product"],
            "stock": ["stock", "quantity", "quantite", "inventory", "available", "disponible", "on_hand"],
            "date": ["date", "day", "jour", "timestamp", "period", "periode", "sold_at"],
            "units_sold": ["units_sold", "sold", "quantity_sold", "ventes", "vendu", "qty", "amount"],
        }

        suggested_mapping: Dict[str, str] = {}
        column_types: Dict[str, str] = {}

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
                    except (ValueError, TypeError):
                        pass

            if pd.api.types.is_numeric_dtype(df[col]):
                column_types[col] = "number"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                column_types[col] = "date"
            else:
                column_types[col] = "string"

        anomalies = []
        for i, row in df.iterrows():
            row_anomalies: Dict[str, str] = {}
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
                "is_excel": is_excel,
            },
        }
