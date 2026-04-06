import { gql } from '@apollo/client';

export const UPDATE_PRODUCT_SETTINGS = gql`
  mutation UpdateProductSettings($id: ID!, $leadTime: Int, $moq: Int) {
    updateProductSettings(id: $id, leadTime: $leadTime, moq: $moq) {
      id
      title
      sku
      leadTime
      moq
      currentStock
    }
  }
`;
