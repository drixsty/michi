import { gql, TypedDocumentNode } from '@apollo/client';
import type { GetProductsQuery, GetProductsQueryVariables } from '@michi/types';

export const GET_PRODUCTS: TypedDocumentNode<GetProductsQuery, GetProductsQueryVariables> = gql`
  query GetProducts($storeId: ID, $id: ID) {
    products(storeId: $storeId, id: $id) {
      id
      sku
      title
      currentStock
      leadTime
      moq
      storeId
      boostFactor
      stockWeight
      warningThreshold
      prediction {
        runRate
        daysOfStock
        predictedStockoutDate
        reorderQuantity
      }
      cleanedDemands {
        date
        correctedUnitsSold
        inventoryLevel
      }
      supplier {
        id
        name
        reliabilityScore
        averageDelayDays
      }
    }
  }
`;
