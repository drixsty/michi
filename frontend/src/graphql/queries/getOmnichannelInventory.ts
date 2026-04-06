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
      channels {
        platform
        productId
        currentStock
        leadTime
        moq
      }
    }
  }
`;

export const EXPORT_REPLENISHMENT_CSV = gql`
  query ExportReplenishmentCsv {
    exportReplenishmentCsv
  }
`;

export const INGEST_WOOCOMMERCE_DATA = gql`
  mutation IngestWoocommerceData($productsCsv: String!, $ordersCsv: String) {
    ingestWoocommerceData(productsCsv: $productsCsv, ordersCsv: $ordersCsv) {
      success
      message
      platform
      productsCount
      salesLogsCount
    }
  }
`;
