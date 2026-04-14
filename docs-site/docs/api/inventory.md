---
id: inventory
title: API — Inventaire
sidebar_label: Inventaire
slug: /api/inventory
---

# Inventaire

## Queries

### `inventory`

```graphql
query GetInventory(
  $storeId: ID
  $platform: String
  $search: String
  $page: Int
  $pageSize: Int
) {
  inventory(
    storeId: $storeId
    platform: $platform
    search: $search
    page: $page
    pageSize: $pageSize
  ) {
    products {
      id sku title currentStock
      costPrice salePrice
      runRate predictedStockoutDate
      reorderQuantity abcRank
      sourcePlatform
    }
    totalCount
  }
}
```

### `product`

```graphql
query GetProduct($id: ID!) {
  product(id: $id) {
    id sku title currentStock
    salesHistory { date quantity }
    predictions { runRate stockoutDate reorderQuantity }
  }
}
```

## Mutations

### `syncInventory`

Déclenche une synchronisation manuelle depuis la plateforme connectée.

```graphql
mutation {
  syncInventory(storeId: "<store_uuid>") {
    success
    productsUpdated
  }
}
```

## Champs produit

| Champ | Type | Description |
|-------|------|-------------|
| `sku` | String | Référence produit |
| `currentStock` | Int | Stock actuel |
| `runRate` | Float | Ventes/jour (run rate) |
| `predictedStockoutDate` | Date | Date de rupture prévue |
| `reorderQuantity` | Int | Quantité de réassort recommandée |
| `abcRank` | String | Rang A/B/C (par profit) |
| `sourcePlatform` | String | SHOPIFY, WOO, AMAZON, CSV |
