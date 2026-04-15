import { gql, TypedDocumentNode } from '@apollo/client';
import type {
  GetDashboardStatsQuery, GetDashboardStatsQueryVariables,
  GetReplenishmentAlertsQuery, GetReplenishmentAlertsQueryVariables,
} from '@michi/types';

export const GET_DASHBOARD_STATS: TypedDocumentNode<GetDashboardStatsQuery, GetDashboardStatsQueryVariables> = gql`
  query GetDashboardStats($storeId: ID) {
    dashboardKpis(storeId: $storeId) {
      totalProducts
      actualStockouts
      urgentAlerts
      predictedStockouts30d
      message
    }
  }
`;

export const FINANCIAL_OVERVIEW: TypedDocumentNode<any, any> = gql`
  query GetFinancialOverview($storeId: ID, $channel: String) {
    financialOverview(storeId: $storeId, channel: $channel) {
      kpis {
        inventoryValueCost
        inventoryValueSale
        revenueAtRisk
        stockCoverageAvgDays
        currency
        isMutualized
      }
      topRisks {
        productId
        sku
        title
        riskValue
        stockoutDate
        reorderQuantity
        daysOfStock
        runRate
        sourcePlatform
      }
      totalRunRate
      totalStock
      healthScore
      activePlatforms
      message
    }
  }
`;

export const GET_REPLENISHMENT_ALERTS: TypedDocumentNode<GetReplenishmentAlertsQuery, GetReplenishmentAlertsQueryVariables> = gql`
  query GetReplenishmentAlerts($storeId: ID) {
    replenishmentAlerts(storeId: $storeId) {
      productId
      runRate
      daysOfStock
      predictedStockoutDate
      reorderQuantity
    }
  }
`;
