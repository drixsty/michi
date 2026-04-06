import { gql } from '@apollo/client';

export const TRIGGER_MOCK_DATA_SYNC = gql`
  mutation TriggerMockDataSync {
    triggerMockDataSync {
      success
      productsCreated
      salesLogsCreated
      message
    }
  }
`;
