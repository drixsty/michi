import { gql } from '@apollo/client';

export const TRIGGER_MOCK_DATA_SYNC = gql`
  mutation TriggerOmnichannelSync {
    triggerOmnichannelSync {
      success
      productsCount
      salesLogsCount
      message
    }
  }
`;
