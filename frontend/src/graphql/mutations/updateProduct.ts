import { gql } from '@apollo/client';

export const UPDATE_PRODUCT_SETTINGS = gql`
  mutation UpdateProductSettings(
    $id: ID!, 
    $leadTime: Int, 
    $moq: Int, 
    $boostFactor: Float,
    $stockWeight: Float
  ) {
    updateProductSettings(
      id: $id, 
      leadTime: $leadTime, 
      moq: $moq, 
      boostFactor: $boostFactor,
      stockWeight: $stockWeight
    ) {
      id
      title
      sku
      leadTime
      moq
      currentStock
      boostFactor
      stockWeight
    }
  }
`;
