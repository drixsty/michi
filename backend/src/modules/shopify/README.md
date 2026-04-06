# Module Shopify — Mock Data Generation

Gère la génération de données de démonstration et la validation du dataset.  
Conçu en **Mock-First** : toutes les fonctionnalités fonctionnent sans intégration Shopify réelle.

---

## Structure

```
modules/shopify/
├── models.py          # SQLAlchemy : Product, SalesLog
├── schemas.py         # Pydantic : SyncResultSchema, ValidationReportSchema
├── mock_generator.py  # Génération déterministe (seed=42)
├── service.py         # ShopifyService : sync + lecture produits
├── validation.py      # DataValidationService : règles R1–R6
├── resolvers.py       # Strawberry GraphQL : types + query + mutation
└── tests/
    ├── test_mock_generator.py   # 14 tests (US 1.1 + 1.2)
    └── test_validation.py       # 11 tests (US 1.4)
```

---

## Pipeline de génération

```
triggerMockDataSync
        │
        ▼
generate_full_mock_dataset(count=50, shop_id)
        │
        ├─► generate_mock_products(50)
        │       └─ 50 produits (SKU, titre, stock, lead_time, MOQ)
        │
        └─► generate_mock_sales(product_id, days=365)  ×50
                ├─ Ventes normales : N(μ=5, σ=2) unités/jour
                ├─ Pics Black Friday (×3–5) : semaine 47 nov.
                ├─ Pics soldes (×3–5) : mi-jan + fin-juin
                └─ Ruptures simulées (10–15% produits, 3–21 jours)
```

---

## Modèles

### `Product`

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID | Clé primaire |
| `shop_id` | UUID | Identifiant du shop (multi-tenant) |
| `sku` | String(100) | Ex : `VET-1000` |
| `title` | String(255) | Nom du produit |
| `current_stock` | Integer | Stock actuel en unités |
| `lead_time` | Integer | Délai fournisseur en jours (7/14/21/30/45) |
| `moq` | Integer | Quantité minimale de commande (5/10/20/50) |

### `SalesLog`

| Colonne | Type | Description |
|---|---|---|
| `id` | UUID | Clé primaire |
| `product_id` | UUID | FK → `products.id` (CASCADE) |
| `date` | Date | Jour de l'entrée |
| `units_sold` | Float | Unités vendues ce jour (0 si rupture) |
| `end_of_day_stock` | Integer | Stock en fin de journée (0 si rupture) |

---

## GraphQL

### Query `products`

```graphql
query {
  products {
    id
    sku
    title
    currentStock
    leadTime
    moq
  }
}
```

### Mutation `triggerMockDataSync`

Réinitialise et régénère le dataset complet du shop connecté.

```graphql
mutation {
  triggerMockDataSync {
    success
    productsCreated
    salesLogsCreated
    message
  }
}
```

### Query `validateMockData`

Contrôle la cohérence du dataset selon 6 règles métier.

```graphql
query {
  validateMockData {
    isValid
    productCount
    salesLogCount
    stockoutRatio
    summary
    issues {
      rule
      severity   # "error" | "warning"
      detail
    }
  }
}
```

**Règles contrôlées :**

| Règle | Description | Sévérité |
|---|---|---|
| R1 | Au moins un produit existe | error |
| R2 | stock ≥ 0, lead_time ∈ {7,14,21,30,45}, MOQ ∈ {5,10,20,50} | error/warning |
| R3 | Exactement 365 entrées par produit | error |
| R4 | Pas de gap de dates dans l'historique | error |
| R5 | `units_sold` ≥ 0 et `end_of_day_stock` ≥ 0 | error |
| R6 | Ratio ruptures entre 8% et 20% | warning |

---

## Commandes

```bash
# Régénérer le dataset démo (50 produits)
make seed-demo

# Régénérer avec 10 produits (tests rapides)
make seed-demo-small

# Régénérer pour un shop spécifique
cd backend && python scripts/seed_demo.py --shop-id <UUID> --count 50

# Lancer les tests du module
pytest src/modules/shopify/tests/ -v

# Coverage
pytest src/modules/shopify/tests/ --cov=src/modules/shopify --cov-report=term
```

---

## Reproductibilité

Le générateur utilise `RANDOM_SEED = 42` (fichier `mock_generator.py`).  
Deux appels successifs à `generate_mock_products()` produisent **exactement les mêmes données**.  
Cela garantit la cohérence entre environnements (dev, CI, démo client).
