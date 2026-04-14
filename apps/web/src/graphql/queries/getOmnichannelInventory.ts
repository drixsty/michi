import { gql } from '@apollo/client';

export const GET_OMNICHANNEL_INVENTORY = gql`
  query GetOmnichannelInventory {
    omnichannelInventory {
      sku
      title
      totalStock
      channelCount
      hasConflict
      dominantRunRate
      totalReorderQuantity
      predictedStockoutDate
      abcRank
      annualGrossProfit
      channels {
        platform
        productId
        currentStock
        leadTime
        moq
        runRate
        stockWeight
      }
    }
  }
`;
