import { gql } from '@apollo/client';

export const UPDATE_PRODUCT_SETTINGS = gql`
  mutation UpdateProductSettings(
    $id: ID!, 
    $leadTime: Int, 
    $moq: Int,
    $boostFactor: Float,
    $stockWeight: Float,
    $costPrice: Float,
    $salePrice: Float,
    $supplierId: ID
  ) {
    updateProductSettings(
      id: $id, 
      leadTime: $leadTime, 
      moq: $moq,
      boostFactor: $boostFactor,
      stockWeight: $stockWeight,
      costPrice: $costPrice,
      salePrice: $salePrice,
      supplierId: $supplierId
    ) {
      id
      title
      sku
      leadTime
      moq
      currentStock
      boostFactor
      stockWeight
      supplier {
        id
        name
      }
    }
  }
`;
