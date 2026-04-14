import { gql } from '@apollo/client';

export const INGEST_CSV_DATA = gql`
  mutation IngestCSVData(
    $storeId: ID!,
    $csvContent: String!, 
    $skuCol: String, 
    $dateCol: String, 
    $salesCol: String, 
    $stockCol: String, 
    $titleCol: String
  ) {
    ingestCsvData(
      storeId: $storeId,
      csvContent: $csvContent,
      skuCol: $skuCol,
      dateCol: $dateCol,
      salesCol: $salesCol,
      stockCol: $stockCol,
      titleCol: $titleCol
    ) {
      success
      message
      platform
      productsCount
      salesLogsCount
    }
  }
`;
