import { gql } from '@apollo/client';

export const GET_ALL_PREDICTIONS = gql`
  query GetAllPredictions {
    predictions {
      productId
      runRate
      daysOfStock
      predictedStockoutDate
      reorderQuantity
    }
  }
`;
