import { gql } from '@apollo/client';

export const GET_PRODUCTS = gql`
  query GetProducts {
    products {
      id
      shopId
      sku
      title
      currentStock
      leadTime
      moq
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
        reliabilityScore
        averageDelayDays
      }
    }
  }
`;
