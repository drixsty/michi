import { gql } from '@apollo/client';

export const GET_PRODUCT_DETAIL = gql`
  query GetProductDetail($id: ID!) {
     productDetail: products(id: $id) {
      id
      sku
      title
      cleanedDemand {
        date
        rawUnitsSold
        correctedUnitsSold
        isStockout
        isOutlier
        correctionType
      }
    }
  }
`;
