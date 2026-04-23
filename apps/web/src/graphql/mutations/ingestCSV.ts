import { gql } from '@apollo/client';

export const SMART_IMPORT = gql`
  mutation SmartImport($input: SmartImportInput!) {
    smartImport(input: $input) {
      success
      message
      productsCount
      salesLogsCount
    }
  }
`;
