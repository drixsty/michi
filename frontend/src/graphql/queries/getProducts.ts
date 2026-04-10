import { gql } from '@apollo/client';

export const GET_PRODUCTS = gql`
  query GetProducts($id: ID) {
    products(id: $id) {
      id
      shopId
      sku
      title
      currentStock
      leadTime
      moq
      warningThreshold
      boostFactor
      stockWeight
      costPrice
      salePrice
      prediction {
        runRate
        daysOfStock
        predictedStockoutDate
        reorderQuantity
      }
      cleanedDemand {
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
