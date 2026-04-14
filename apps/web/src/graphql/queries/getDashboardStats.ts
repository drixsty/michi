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
