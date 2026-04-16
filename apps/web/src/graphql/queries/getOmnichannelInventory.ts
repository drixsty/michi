import { gql, TypedDocumentNode } from '@apollo/client';
import type { GetOmnichannelInventoryQuery, GetOmnichannelInventoryQueryVariables } from '@michi/types';

export const GET_OMNICHANNEL_INVENTORY: TypedDocumentNode<GetOmnichannelInventoryQuery, GetOmnichannelInventoryQueryVariables> = gql`
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
      demandSigma
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
