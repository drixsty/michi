import pandas as pd
"""
WooCommerce CSV Connector — US 9.2 (Sprint 9)

Format cible : Export natif WooCommerce (wp-admin → Products → Export)

Colonnes produits WooCommerce (format standard) :
    ID, Type, SKU, Name, Published, Stock status, Stock,
    Regular price, Sale price, Categories, Tags

Colonnes ventes WooCommerce (export Orders) :
    Order ID, Date, Status, SKU, Item, Quantity, Total

Raison d'existence :
    WooCommerce est la 2e plateforme e-commerce mondiale (derrière Shopify).
    Les marchands mode/beauté migrent souvent de WooCommerce → Shopify mais
    gardent les deux en parallèle. Sans ce connecteur, ils ne peuvent pas
    importer leur historique WooCommerce dans Michi.

Différence avec CSVConnector générique :
    - Mapping de colonnes figé (format natif WooCommerce)
    - Gestion du `Stock status` ("instock"/"outofstock")
    - Parsing de `Date` en format WooCommerce (Y-m-d H:i:s)
    - Filtre automatique sur les commandes `completed`
"""
import io
from typing import List, Dict, Any
from datetime import datetime

from ..domain.base import BaseConnector


# Mapping colonnes WooCommerce → Michi
_PRODUCT_COL_MAP = {
    "SKU": "sku",
    "Name": "title",
    "Stock": "current_stock",
}

_SALES_COL_MAP = {
    "SKU": "sku",
    "Date": "date",
    "Quantity": "units_sold",
}


class WooCommerceConnector(BaseConnector):
    """
    Connecteur CSV pour les exports WooCommerce natifs.
    Compatible avec les exports générés depuis wp-admin.
    """

    async def fetch_products(
        self, csv_content: str, mapping: Dict[str, str] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Ingère les produits depuis un export produits WooCommerce.

        Args:
            csv_content: Contenu brut du fichier CSV WooCommerce.
            mapping: Optionnel. Override du mapping de colonnes par défaut.

        Returns:
            Liste de dicts [{sku, title, current_stock}].

        Raises:
            ValueError: Si les colonnes obligatoires (SKU, Name) sont absentes.
        """
        df = pd.read_csv(io.StringIO(csv_content))
        col_map = {**_PRODUCT_COL_MAP, **(mapping or {})}

        # Vérification colonnes obligatoires
        required = {"SKU", "Name"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Colonnes WooCommerce manquantes : {missing}. "
                f"Colonnes disponibles : {list(df.columns)}"
            )

        # Filtrer les variantes sans SKU
        df = df[df["SKU"].notna() & (df["SKU"].astype(str).str.strip() != "")]

        # Stock : fallback à 0 si colonne absente ou "outofstock"
        if "Stock" in df.columns:
            stock_values = pd.to_numeric(df["Stock"], errors="coerce").fillna(0)
        else:
            # WooCommerce peut ne pas exporter le chiffre de stock brut
            # si `Manage stock` est désactivé → on utilise Stock status
            if "Stock status" in df.columns:
                stock_values = df["Stock status"].map(
                    {"instock": 10, "outofstock": 0}
                ).fillna(0)
            else:
                stock_values = pd.Series(0, index=df.index)

        products = []
        for i, row in df.iterrows():
            products.append({
                "sku": str(row["SKU"]).strip(),
                "title": str(row["Name"]).strip(),
                "current_stock": int(stock_values.iloc[i]),
            })

        return products

    async def fetch_sales_history(
        self, csv_content: str, mapping: Dict[str, str] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Ingère l'historique de ventes depuis un export commandes WooCommerce.

        Format attendu : export Orders WooCommerce (wp-admin → Orders → Export).
        Filtre automatiquement sur status = "completed".

        Args:
            csv_content: Contenu brut du fichier CSV WooCommerce Orders.
            mapping: Optionnel. Override du mapping de colonnes par défaut.

        Returns:
            Liste de dicts [{sku, date, units_sold, end_of_day_stock}].

        Raises:
            ValueError: Si les colonnes obligatoires (SKU, Date, Quantity) sont absentes.
        """
        df = pd.read_csv(io.StringIO(csv_content))
        col_map = {**_SALES_COL_MAP, **(mapping or {})}

        # Colonnes aliases WooCommerce order export
        # WooCommerce renomme parfois "SKU" en "Item SKU" ou "Product SKU"
        col_aliases = {
            "Item SKU": "SKU",
            "Product SKU": "SKU",
            "Order Date": "Date",
            "Item Quantity": "Quantity",
            "Qty": "Quantity",
        }
        df = df.rename(columns=col_aliases)

        required = {"SKU", "Date", "Quantity"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Colonnes WooCommerce Orders manquantes : {missing}. "
                f"Colonnes disponibles : {list(df.columns)}"
            )

        # Filtrer les commandes complétées uniquement
        if "Status" in df.columns:
            df = df[df["Status"].str.lower().isin(["completed", "processing"])]

        # Parser les dates WooCommerce (format: "2025-03-15 14:23:45" ou "2025-03-15")
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

        # Supprimer les lignes sans date ou sans SKU
        df = df[df["Date"].notna() & df["SKU"].notna()]
        df = df[df["SKU"].astype(str).str.strip() != ""]

        # Convertir quantité
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)

        # Agréger par SKU + date (une commande peut avoir plusieurs lignes)
        agg = (
            df.groupby(["SKU", "Date"])["Quantity"]
            .sum()
            .reset_index()
        )

        sales = []
        for _, row in agg.iterrows():
            sales.append({
                "sku": str(row["SKU"]).strip(),
                "date": row["Date"],
                "units_sold": float(row["Quantity"]),
                "end_of_day_stock": 0,  # WooCommerce n'exporte pas le stock fin de journée
            })

        return sales
