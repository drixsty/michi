import { gql } from '@apollo/client';
import type { GetProductsQuery, GetProductsQueryVariables } from '@michi/types';
import type { TypedDocumentNode } from '@apollo/client';

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
      warningThreshold
      prediction {
        runRate
        daysOfStock
        predictedStockoutDate
        reorderQuantity
      }
    }
  }
`;
