import { gql } from '@apollo/client';

export const GET_ALL_PREDICTIONS = gql`
  query GetAllPredictions($storeId: ID!) {
    predictions(storeId: $storeId) {
      productId
      runRate
      daysOfStock
      predictedStockoutDate
      reorderQuantity
    }
  }
`;
