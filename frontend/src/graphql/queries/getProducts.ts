import { gql } from '@apollo/client';

export const GET_PRODUCTS = gql`
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
      supplier {
        id
        name
      }
    }
  }
`;
