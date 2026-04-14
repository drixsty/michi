---
id: decisions
title: API — Centre Décisionnel
sidebar_label: Centre Décisionnel
slug: /api/decisions
---

# Centre Décisionnel

## Query `decisionCenter`

```graphql
query GetDecisionCenter($channel: String) {
  decisionCenter(channel: $channel) {
    kpis {
      inventoryValueCost
      inventoryValueSale
      revenueAtRisk
      stockCoverageAvgDays
      currency
      isMutualized
    }
    healthScore
    totalRunRate
    totalStock
    topRisks {
      productId sku title
      riskValue stockoutDate
      reorderQuantity daysOfStock
      runRate supplierName
      sourcePlatform costPrice salePrice
    }
    activePlatforms
    capitalBreakdown {
      platform value
    }
    message
  }
}
```

## KPIs financiers

| KPI | Formule |
|-----|---------|
| `inventoryValueCost` | Σ(stock × cost_price) |
| `inventoryValueSale` | Σ(stock × sale_price) |
| `revenueAtRisk` | Σ(reorder_qty × sale_price) pour produits à risque |
| `stockCoverageAvgDays` | mean(stock / run_rate) pour SKUs avec run_rate > 0 |

## Health Score

Score de 0 à 100 calculé par `intelligence/analytics/health_score.py`.

```
healthScore = round((avail × 0.5 + rot × 0.3 + out_ratio × 0.2) × 100)
```

| Score | Interprétation |
|-------|----------------|
| 90–100 | Excellent |
| 70–89 | Bon |
| 50–69 | Attention requise |
| < 50 | Critique |
