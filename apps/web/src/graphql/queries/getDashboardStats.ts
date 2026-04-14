import { gql } from '@apollo/client';

export const GET_DASHBOARD_STATS = gql`
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

export const GET_REPLENISHMENT_ALERTS = gql`
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
