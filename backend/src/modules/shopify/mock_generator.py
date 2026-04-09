"""
Mock Shopify Data Generator
Génère des produits et historiques de ventes réalistes pour la démo.

Stratégie:
- 50 produits mode/beauté avec SKU, titre, stock
- 365 jours d'historique par produit
- 10-15% des produits ont des ruptures simulées (3-21 jours)
- Outliers Black Friday / soldes (x3-x5 ventes)
"""
import random
import uuid
from datetime import date, timedelta
from typing import Optional
import numpy as np

# Seed fixe pour reproductibilité
RANDOM_SEED = 42

# Catalogue mock mode/beauté
PRODUCT_CATALOG = [
    ("T-shirt Basique Blanc", "VET"),
    ("Jean Slim Bleu", "VET"),
    ("Robe Fleurie Été", "VET"),
    ("Veste en Lin Beige", "VET"),
    ("Pull Col Roulé Noir", "VET"),
    ("Chemise Oxford Bleue", "VET"),
    ("Short Cargo Kaki", "VET"),
    ("Blazer Croisé Gris", "VET"),
    ("Legging Sport Noir", "VET"),
    ("Manteau Laine Camel", "VET"),
    ("Sneakers Blanches Classiques", "CHAU"),
    ("Bottines Chelsea Noires", "CHAU"),
    ("Sandales Plates Nude", "CHAU"),
    ("Mocassins Cuir Marron", "CHAU"),
    ("Espadrilles Rayées Marine", "CHAU"),
    ("Sérum Vitamine C 30ml", "BEAU"),
    ("Crème Hydratante SPF50", "BEAU"),
    ("Huile Sèche Corps 100ml", "BEAU"),
    ("Fond de Teint Longue Tenue", "BEAU"),
    ("Mascara Volume Extrême", "BEAU"),
    ("Rouge à Lèvres Mat Rose", "BEAU"),
    ("Palette Fards à Paupières", "BEAU"),
    ("Eau Micellaire 400ml", "BEAU"),
    ("Exfoliant Visage 75ml", "BEAU"),
    ("Crème Contour des Yeux", "BEAU"),
    ("Sac à Main Structuré Noir", "ACC"),
    ("Ceinture Cuir Cognac", "ACC"),
    ("Écharpe Cachemire Grise", "ACC"),
    ("Chapeau Bob Paille", "ACC"),
    ("Lunettes de Soleil Cat-Eye", "ACC"),
    ("Collier Doré Minimaliste", "BIJ"),
    ("Boucles d'Oreilles Perles", "BIJ"),
    ("Bracelet Manchette Argenté", "BIJ"),
    ("Bague Empilable Or Rose", "BIJ"),
    ("Montre Minimaliste Blanche", "BIJ"),
    ("Coffret Parfum Floral 50ml", "PARF"),
    ("Eau de Toilette Boisé 100ml", "PARF"),
    ("Brume Corps Vanille", "PARF"),
    ("Désodorisant Naturel Citron", "PARF"),
    ("Gel Douche Moussant Amande", "SOIN"),
    ("Shampoing Éclat Couleur", "SOIN"),
    ("Après-Shampoing Hydratant", "SOIN"),
    ("Masque Capillaire Kératine", "SOIN"),
    ("Sérum Anti-Chute", "SOIN"),
    ("Gommage Corps Sucre Coco", "SOIN"),
    ("Lotion Tonique Rééquilibrante", "SOIN"),
    ("BB Crème Multi-Actions", "BEAU"),
    ("Primer Pores Affinés", "BEAU"),
    ("Poudre Fixatrice Translucide", "BEAU"),
    ("Crayon Yeux Waterproof", "BEAU"),
]

# Jours de pic de ventes (Black Friday semaine 47, soldes mi-janvier et mi-juin)
def _is_peak_day(d: date) -> bool:
    """Retourne True si le jour est un jour de forte demande."""
    # Black Friday (semaine 47 novembre)
    if d.month == 11 and 24 <= d.day <= 30:
        return True
    # Soldes d'hiver (2e semaine janvier)
    if d.month == 1 and 8 <= d.day <= 21:
        return True
    # Soldes d'été (dernière semaine juin, première juillet)
    if (d.month == 6 and d.day >= 25) or (d.month == 7 and d.day <= 7):
        return True
    return False


def generate_mock_products(count: int = 50, shop_id: Optional[str] = None) -> list[dict]:
    """
    Génère une liste de produits mock pour un shop.

    Args:
        count: Nombre de produits à générer (défaut: 50).
        shop_id: UUID du shop propriétaire. Généré si None.

    Returns:
        Liste de dicts compatibles avec le modèle Product.

    Notes:
        - Utilise RANDOM_SEED=42 pour reproductibilité.
        - Stock initial entre 0 et 200 unités.
        - Lead time entre 7 et 45 jours.
        - MOQ entre 5 et 50 unités.
    """
    rng = random.Random(RANDOM_SEED)
    _shop_id = shop_id or str(uuid.uuid4())

    catalog = PRODUCT_CATALOG[:count] if count <= len(PRODUCT_CATALOG) else (
        PRODUCT_CATALOG + [(f"Produit Extra {i}", "MISC") for i in range(count - len(PRODUCT_CATALOG))]
    )

    products = []
    for i, (title, category) in enumerate(catalog[:count]):
        product_id = str(uuid.uuid4())
        sku = f"{category}-{1000 + i:04d}"
        products.append({
            "id": product_id,
            "shop_id": _shop_id,
            "sku": sku,
            "title": title,
            "current_stock": rng.randint(0, 200),
            "lead_time": rng.choice([7, 14, 21, 30, 45]),
            "moq": rng.choice([5, 10, 20, 50]),
            "source_platform": "shopify",
        })

    return products


def generate_mock_sales(product_id: str, sku: Optional[str] = None, days: int = 365, has_stockout: bool = False) -> list[dict]:
    """
    Génère l'historique de ventes quotidiennes pour un produit.

    Args:
        product_id: UUID ou SKU du produit.
        sku: SKU optionnel pour lier les logs lors de la sync intelligente.
        days: Nombre de jours d'historique (défaut: 365).
        has_stockout: Si True, génère 1-3 ruptures aléatoires.

    Returns:
        Liste de dicts compatibles avec le modèle SalesLog (incluant le SKU).

    Notes:
        - Ventes journalières de base : distribution normale (μ=5, σ=2).
        - Jours peak (Black Friday, soldes) : ventes x3 à x5.
        - Rupture simulée : units_sold=0, end_of_day_stock=0 pendant 3-21 jours.
    """
    rng = random.Random(RANDOM_SEED + hash(product_id) % 10000)
    np_rng = np.random.default_rng(RANDOM_SEED + hash(product_id) % 10000)

    today = date.today()
    start_date = today - timedelta(days=days - 1)

    # Vente de base ~5 unités/jour
    base_mean = rng.uniform(2, 10)
    base_std = base_mean * 0.4

    # Construire les périodes de rupture
    stockout_periods: list[tuple[date, date]] = []
    if has_stockout:
        num_stockouts = rng.randint(1, 3)
        for _ in range(num_stockouts):
            offset = rng.randint(30, days - 30)
            length = rng.randint(3, 21)
            stockout_start = start_date + timedelta(days=offset)
            stockout_end = stockout_start + timedelta(days=length)
            stockout_periods.append((stockout_start, stockout_end))

    def in_stockout(d: date) -> bool:
        return any(s <= d <= e for s, e in stockout_periods)

    stock = rng.randint(50, 200)
    sales_logs = []

    for i in range(days):
        current_date = start_date + timedelta(days=i)

        if in_stockout(current_date):
            units_sold = 0.0
            stock = 0
        else:
            units = float(np_rng.normal(base_mean, base_std))
            if _is_peak_day(current_date):
                units *= rng.uniform(3.0, 5.0)
            units = max(0.0, round(units, 1))

            units_sold = units
            stock = max(0, stock - int(units))

        log = {
            "product_id": product_id,
            "date": current_date,
            "units_sold": units_sold,
            "end_of_day_stock": int(stock),
        }
        if sku:
            log["sku"] = sku
        sales_logs.append(log)

    return sales_logs


def generate_full_mock_dataset(count: int = 50, shop_id: Optional[str] = None) -> tuple[list[dict], list[dict]]:
    """
    Génère le dataset complet : produits + historique ventes.

    Args:
        count: Nombre de produits.
        shop_id: UUID du shop.

    Returns:
        Tuple (products, sales_logs).

    Notes:
        - 10-15% des produits auront des ruptures simulées.
    """
    rng = random.Random(RANDOM_SEED)
    products = generate_mock_products(count=count, shop_id=shop_id)

    # 10-15% ont des ruptures
    stockout_count = int(count * rng.uniform(0.10, 0.15))
    stockout_ids = set(p["id"] for p in rng.sample(products, stockout_count))

    all_sales: list[dict] = []
    for product in products:
        has_stockout = product["id"] in stockout_ids
        sku = product["sku"]  # Nouveau : on récupère le SKU
        logs = generate_mock_sales(product["id"], sku=sku, days=365, has_stockout=has_stockout)
        all_sales.extend(logs)

    return products, all_sales
