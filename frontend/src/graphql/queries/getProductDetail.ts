import { gql } from '@apollo/client';

export const GET_PRODUCT_DETAIL = gql`
  query GetProductDetail($storeId: ID, $id: ID!) {
     productDetail: products(storeId: $storeId, id: $id) {
      id
      sku
      title
      currentStock
      leadTime
      moq
      boostFactor
      stockWeight
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
      cleanedDemands {
        date
        rawUnitsSold
        correctedUnitsSold
        inventoryLevel
        isStockout
        isOutlier
        correctionType
      }
      channels {
        platform
        productId
        currentStock
        runRate
        leadTime
        moq
        stockWeight
      }
    }
  }
`;
