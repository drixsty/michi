import { gql, TypedDocumentNode } from '@apollo/client';
import type { TriggerOmnichannelSyncMutation, TriggerOmnichannelSyncMutationVariables } from '@michi/types';

export const TRIGGER_MOCK_DATA_SYNC: TypedDocumentNode<TriggerOmnichannelSyncMutation, TriggerOmnichannelSyncMutationVariables> = gql`
  mutation TriggerOmnichannelSync($storeId: ID!) {
    triggerOmnichannelSync(storeId: $storeId) {
      success
      productsCount
      salesLogsCount
      message
    }
  }
`;
