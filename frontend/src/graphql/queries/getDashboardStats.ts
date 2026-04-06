import { gql } from '@apollo/client';

export const GET_DASHBOARD_STATS = gql`
  query GetDashboardStats {
    dashboardKpis {
      totalProducts
      actualStockouts
      urgentAlerts
      predictedStockouts30d
      message
    }
  }
`;

export const GET_REPLENISHMENT_ALERTS = gql`
  query GetReplenishmentAlerts {
    replenishmentAlerts {
      productId
      runRate
      daysOfStock
      predictedStockoutDate
      reorderQuantity
    }
  }
`;
