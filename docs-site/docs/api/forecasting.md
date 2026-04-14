---
id: forecasting
title: API — Prévisions
sidebar_label: Prévisions
slug: /api/forecasting
---

# Prévisions

## Query `forecasting`

```graphql
query GetForecasting($storeId: ID) {
  forecasting(storeId: $storeId) {
    predictions {
      productId sku
      runRate
      predictedStockoutDate
      reorderQuantity
      coverageDays
    }
    mapeScore
    lastRunAt
  }
}
```

## Mutation `runForecasting`

Déclenche le pipeline de prévision pour une organisation.

```graphql
mutation {
  runForecasting {
    success
    productsProcessed
    mapeScore
  }
}
```

## Champs prédiction

| Champ | Type | Description |
|-------|------|-------------|
| `runRate` | Float | Ventes journalières (médiane adaptative 7j/30j) |
| `predictedStockoutDate` | Date | Date estimée de rupture |
| `reorderQuantity` | Int | Quantité à commander |
| `coverageDays` | Float | Jours de stock restants |
