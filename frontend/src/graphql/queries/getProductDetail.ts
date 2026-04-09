import { gql } from '@apollo/client';

export const GET_PRODUCT_DETAIL = gql`
  query GetProductDetail($id: ID!) {
     productDetail: products(id: $id) {
      id
      sku
      title
      currentStock
      leadTime
      moq
      warningThreshold
      supplier {
        name
        reliabilityScore
      }
      prediction {
        runRate
        predictedStockoutDate
        reorderQuantity
      }
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
