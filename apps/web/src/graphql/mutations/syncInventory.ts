import { gql } from '@apollo/client';

export const TRIGGER_MOCK_DATA_SYNC = gql`
  mutation TriggerOmnichannelSync($storeId: ID!) {
    triggerOmnichannelSync(storeId: $storeId) {
      success
      productsCount
      salesLogsCount
      message
    }
  }
`;
