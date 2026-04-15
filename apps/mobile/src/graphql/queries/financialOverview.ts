import { gql } from '@apollo/client';

export const FINANCIAL_OVERVIEW = gql`
  query GetFinancialOverview($storeId: ID) {
    financialOverview(storeId: $storeId) {
      inventoryValue
      revenueAtRisk
      stockHealthScore
      currency
    }
  }
`;
