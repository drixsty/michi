import { gql, TypedDocumentNode } from '@apollo/client';
import type { GetAllPredictionsQuery, GetAllPredictionsQueryVariables } from '@michi/types';

export const GET_ALL_PREDICTIONS: TypedDocumentNode<GetAllPredictionsQuery, GetAllPredictionsQueryVariables> = gql`
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
