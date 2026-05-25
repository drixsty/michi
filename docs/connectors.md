# Connecteurs Marketplace — Architecture & Référence Technique

**Version :** 2.0  
**Date :** Mai 2026  
**Module :** `apps/api/src/modules/ingestion/`

---

## Table des Matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture hexagonale](#2-architecture-hexagonale)
3. [Contrat BaseConnector](#3-contrat-baseconnector)
4. [Plateformes supportées](#4-plateformes-supportées)
5. [Mode Mock vs Production](#5-mode-mock-vs-production)
6. [Flux d'ingestion complet](#6-flux-dingestion-complet)
7. [Stockage des credentials](#7-stockage-des-credentials)
8. [Rate limits & retry](#8-rate-limits--retry)
9. [Ajouter un nouveau connecteur](#9-ajouter-un-nouveau-connecteur)
10. [Tests](#10-tests)

---

## 1. Vue d'ensemble

Le module **Ingestion** est le pont entre les plateformes e-commerce et le modèle unifié Michi. Il suit le pattern **Port/Adapter** (hexagonale) : le domaine définit une interface (`BaseConnector`), et chaque plateforme implémente cet adapter.

```
Shopify ─────┐
WooCommerce ─┤                     ┌──────────────────────┐
CSV/Excel ───┤──► ConnectorFactory ──► IngestionService ──► InventoryService
Amazon ──────┤                     └──────────────────────┘
eBay ────────┤                              │
Etsy ────────┘                              ▼
                                    PostgreSQL (products,
                                    sales_logs, predictions)
```

---

## 2. Architecture hexagonale

```
ingestion/
├── domain/                        ← Port (interfaces pures, pas de framework)
│   ├── base.py                    ← BaseConnector ABC
│   └── schemas.py                 ← IngestedProduct, IngestedSale, IngestionResult
│
├── connectors/                    ← Adapters (implémentations par plateforme)
│   ├── shopify.py                 ← Shopify Admin REST API 2024-01
│   ├── woocommerce.py             ← CSV export natif WooCommerce
│   ├── csv.py                     ← Universel CSV/Excel + IA fuzzy matching
│   ├── amazon.py                  ← Amazon SP-API (LWA OAuth)
│   ├── ebay.py                    ← eBay REST API (OAuth 2.0)
│   └── etsy.py                    ← Etsy Open API v3 (PKCE)
│
└── application/                   ← Orchestration
    ├── factory.py                 ← ConnectorFactory (routing plateforme → classe)
    ├── service.py                 ← IngestionService (orchestrateur principal)
    └── ingestion_service.py       ← Service alternatif (batch store sync)
```

---

## 3. Contrat BaseConnector

Toute plateforme doit implémenter ces 4 méthodes :

```python
class BaseConnector(ABC):

    async def validate_connection(
        self, credentials: Dict[str, Any]
    ) -> bool:
        """
        Vérifie que les credentials permettent d'accéder à l'API.
        Appelé lors de la connexion initiale d'un store.
        """

    async def fetch_products(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedProduct]:
        """
        Retourne la liste normalisée des produits.
        Les connecteurs CSV reçoivent le contenu via kwargs['csv_content'].
        """

    async def fetch_sales_history(
        self,
        product_sku: str,
        shop_id: str,
        days: int = 365,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[IngestedSale]:
        """
        Retourne l'historique quotidien des ventes pour un SKU.
        Résultat trié par date croissante.
        """

    async def fetch_all_data(
        self,
        shop_id: str,
        credentials: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Batch optimisé : retourne produits + ventes.
        {"products": List[IngestedProduct], "sales": List[IngestedSale]}
        """
```

### Schemas normalisés

```python
class IngestedProduct(BaseModel):
    sku: str                         # Identifiant unique produit
    title: str                       # Nom du produit
    description: Optional[str]       # Description courte (500 chars max)
    barcode: Optional[str]           # EAN/UPC
    price: float = 0.0               # Prix de vente TTC
    current_stock: int = 0           # Stock disponible
    category: Optional[str]          # Catégorie plateforme
    image_url: Optional[str]         # URL première image
    vendor: Optional[str]            # Nom de la marque/fournisseur

class IngestedSale(BaseModel):
    sku: str                         # SKU du produit vendu
    date: date                       # Date de la vente (YYYY-MM-DD)
    units_sold: int                  # Quantité vendue ce jour
    stock_at_end: Optional[int]      # Stock fin de journée (si disponible)
    order_id: Optional[str]          # ID commande source
```

---

## 4. Plateformes supportées

| Plateforme | Classe | Auth | Mode mock | Env var |
|---|---|---|---|---|
| Shopify | `ShopifyConnector` | OAuth Access Token | `USE_MOCK_SHOPIFY` | `true` (dev) |
| WooCommerce | `WooCommerceConnector` | Fichier CSV | N/A | — |
| CSV/Excel | `CSVConnector` | Fichier | N/A | — |
| Amazon | `AmazonConnector` | LWA OAuth (refresh_token) | `USE_MOCK_AMAZON` | `true` (dev) |
| eBay | `EbayConnector` | OAuth 2.0 (refresh_token) | `USE_MOCK_EBAY` | `true` (dev) |
| Etsy | `EtsyConnector` | OAuth 2.0 PKCE | `USE_MOCK_ETSY` | `true` (dev) |
| Faire | *(à venir)* | OAuth 2.0 | — | — |

### Registre ConnectorFactory

```python
# apps/api/src/modules/ingestion/application/factory.py

_connectors = {
    "SHOPIFY":     ShopifyConnector,
    "WOOCOMMERCE": WooCommerceConnector,
    "CSV":         CSVConnector,
    "AMAZON":      AmazonConnector,
    "EBAY":        EbayConnector,
    "ETSY":        EtsyConnector,
}
```

---

## 5. Mode Mock vs Production

Tous les connecteurs API (Shopify, Amazon, eBay, Etsy) supportent un **mode mock** activé par variable d'environnement. En mode mock, les données sont générées par `mock_generator.py` — aucun appel réseau réel.

```bash
# .env (développement — valeurs par défaut)
USE_MOCK_SHOPIFY=true
USE_MOCK_AMAZON=true
USE_MOCK_EBAY=true
USE_MOCK_ETSY=true

# .env.production (production)
USE_MOCK_SHOPIFY=false
USE_MOCK_AMAZON=false
USE_MOCK_EBAY=false
USE_MOCK_ETSY=false
```

Le mode mock est décidé **dans le constructeur** du connecteur :

```python
class AmazonConnector(BaseConnector):
    def __init__(self):
        self._use_mock = os.getenv("USE_MOCK_AMAZON", "true").lower() == "true"
```

Ainsi, chaque appel à `fetch_products` court-circuite l'API si `_use_mock = True` :

```python
async def fetch_products(self, shop_id, credentials=None, **kwargs):
    if self._use_mock or not credentials:
        return self._mock_products(shop_id)  # ← données locales
    # ... appels API réels
```

---

## 6. Flux d'ingestion complet

### Déclenchement via IngestionService

```python
# Exemple : ingestion Amazon depuis un resolver GraphQL
await ingestion_service.ingest_from_platform(
    platform="AMAZON",
    shop_id=str(store.id),
    organization_id=org.id,
    credentials={
        "lwa_client_id": decrypted_client_id,
        "lwa_client_secret": decrypted_client_secret,
        "lwa_refresh_token": decrypted_refresh_token,
        "marketplace_id": "A13V1IB3VIYZZH",
    }
)
```

### Séquence d'exécution

```
1. IngestionService.ingest_from_platform("AMAZON", ...)
        │
2. ConnectorFactory.get_connector("AMAZON")
        │  → AmazonConnector()
        │
3. connector.fetch_all_data(shop_id, credentials=credentials)
        │
        ├─ 3a. _get_access_token(credentials)   ← LWA token refresh (cache 55 min)
        ├─ 3b. fetch_products()                 ← /catalog/2022-04-01/items (paginated)
        │       └─ _enrich_with_inventory()     ← /fba/inventory/v1/summaries
        └─ 3c. fetch_sales_history() × N skus  ← /sales/v1/orderMetrics
        │
4. Subscription Guard (BASIC plan : max 100 produits)
        │
5. PlatformSource enum resolution (AMAZON → PlatformSource.AMAZON)
        │
6. InventoryService.upsert_inventory_data()
        │  → INSERT/UPDATE products
        │  → INSERT sales_logs
        │
7. Retour : {"products_count": N, "sales_logs_count": M, "status": "Success"}
```

---

## 7. Stockage des credentials

Les secrets ne sont **jamais** stockés en clair. Le modèle `StoreCredential` utilise des champs chiffrés :

```python
class StoreCredential(Base):
    __tablename__ = "store_credentials"

    encrypted_access_token  = Column(String(1024))  # access_token / refresh_token
    encrypted_api_key       = Column(String(1024))  # client_id / api_key
    encrypted_api_secret    = Column(String(1024))  # client_secret / api_secret
    meta                    = Column(JSON)           # marketplace_id, shop_domain, etc.
```

### Mapping par plateforme

| Plateforme | encrypted_access_token | encrypted_api_key | encrypted_api_secret | meta |
|---|---|---|---|---|
| Shopify | `shopify_access_token` | — | — | `{"shopify_domain": "..."}` |
| Amazon | `lwa_refresh_token` | `lwa_client_id` | `lwa_client_secret` | `{"marketplace_id": "...", "seller_id": "..."}` |
| eBay | `ebay_refresh_token` | `ebay_client_id` | `ebay_client_secret` | `{"marketplace_id": "EBAY_FR"}` |
| Etsy | `etsy_refresh_token` | `etsy_client_id` | — | `{"etsy_shop_id": "..."}` |

### Déchiffrement avant passage au connecteur

```python
# Dans le resolver GraphQL (à implémenter)
from core.security.encryption import decrypt_field

credentials = {
    "lwa_client_id":     decrypt_field(cred.encrypted_api_key),
    "lwa_client_secret": decrypt_field(cred.encrypted_api_secret),
    "lwa_refresh_token": decrypt_field(cred.encrypted_access_token),
    "marketplace_id":    cred.meta.get("marketplace_id"),
}
```

---

## 8. Rate limits & retry

Chaque connecteur API est décoré avec `@retry(retries=3, delay=N)` et respecte un délai entre requêtes :

| Plateforme | Délai inter-requêtes | Retry | Token cache |
|---|---|---|---|
| Shopify | 0.5s | 3 × | N/A (token permanent) |
| Amazon | 1.1s | 3 × | 55 min (LWA token) |
| eBay | 0.5s | 3 × | 90 min (OAuth token) |
| Etsy | 0.12s | 3 × | 55 min (OAuth token) |

Le décorateur `@retry` est défini dans `core/utils.py` :

```python
def retry(retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:
                        raise
                    await asyncio.sleep(delay * (attempt + 1))
        return wrapper
    return decorator
```

---

## 9. Ajouter un nouveau connecteur

### Étape 1 — Créer le fichier connecteur

```python
# apps/api/src/modules/ingestion/connectors/faire.py

class FaireConnector(BaseConnector):

    def __init__(self):
        self._use_mock = os.getenv("USE_MOCK_FAIRE", "true").lower() == "true"

    async def validate_connection(self, credentials):
        ...

    async def fetch_products(self, shop_id, credentials=None, **kwargs):
        if self._use_mock or not credentials:
            return self._mock_products(shop_id)
        # Appels API Faire v2
        ...

    async def fetch_sales_history(self, product_sku, shop_id, days=365, credentials=None, **kwargs):
        ...

    async def fetch_all_data(self, shop_id, credentials=None, **kwargs):
        ...
```

### Étape 2 — Enregistrer dans ConnectorFactory

```python
# factory.py
from ..connectors.faire import FaireConnector

_connectors = {
    ...
    "FAIRE": FaireConnector,
}
```

### Étape 3 — Ajouter à PlatformSource

```python
# modules/inventory/domain/entities.py
class PlatformSource(Enum):
    ...
    FAIRE = "FAIRE"  # déjà ajouté ✅
```

### Étape 4 — Variables d'environnement

```bash
USE_MOCK_FAIRE=true   # .env dev
USE_MOCK_FAIRE=false  # .env.production
```

---

## 10. Tests

### Structure attendue

```
apps/api/tests/
└── modules/
    └── ingestion/
        ├── connectors/
        │   ├── test_shopify_connector.py
        │   ├── test_amazon_connector.py
        │   ├── test_ebay_connector.py
        │   └── test_etsy_connector.py
        └── application/
            ├── test_factory.py
            └── test_ingestion_service.py
```

### Exemple de test (mode mock)

```python
# test_amazon_connector.py
import pytest
from modules.ingestion.connectors.amazon import AmazonConnector

@pytest.mark.asyncio
async def test_fetch_products_mock():
    connector = AmazonConnector()  # USE_MOCK_AMAZON=true par défaut en test
    products = await connector.fetch_products("shop-id-123")
    assert len(products) > 0
    assert all(p.sku for p in products)
    assert all(p.current_stock >= 0 for p in products)

@pytest.mark.asyncio
async def test_validate_connection_mock():
    connector = AmazonConnector()
    result = await connector.validate_connection({})
    assert result is True
```

### Exemple de test (production avec VCR.py)

```python
# test_amazon_connector_prod.py
import pytest
import vcr

@pytest.mark.vcr
@pytest.mark.asyncio
async def test_fetch_products_production(cassette_dir):
    """Test avec réponse API enregistrée (VCR cassette)."""
    connector = AmazonConnector()
    connector._use_mock = False
    credentials = {
        "lwa_client_id": "test-client-id",
        "lwa_client_secret": "test-secret",
        "lwa_refresh_token": "test-refresh",
        "marketplace_id": "A13V1IB3VIYZZH",
    }
    products = await connector.fetch_products("shop-123", credentials=credentials)
    assert isinstance(products, list)
```

---

## Guides d'inscription par plateforme

- [Shopify → Guide inscription](registration_shopify.md)
- [Amazon SP-API → Guide inscription](registration_amazon.md)
- [eBay → Guide inscription](registration_ebay.md)
- [Etsy → Guide inscription](registration_etsy.md)

---

*Voir aussi : [architecture.md](architecture.md) — Architecture globale Michi*
