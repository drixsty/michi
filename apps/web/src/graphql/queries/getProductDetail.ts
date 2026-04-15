import { gql, TypedDocumentNode } from '@apollo/client';
import type { GetProductDetailQuery, GetProductDetailQueryVariables } from '@michi/types';

export const GET_PRODUCT_DETAIL: TypedDocumentNode<GetProductDetailQuery, GetProductDetailQueryVariables> = gql`
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
      costPrice
      salePrice
      warningThreshold
      supplier {
        name
        reliabilityScore
      }
      prediction {
        runRate
        daysOfStock
        predictedStockoutDate
        reorderQuantity
        demandSigma
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
