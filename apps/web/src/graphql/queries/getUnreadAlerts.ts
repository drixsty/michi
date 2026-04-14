import { gql, TypedDocumentNode } from '@apollo/client';
import type {
  GetUnreadAlertsQuery, GetUnreadAlertsQueryVariables,
  MarkAlertAsReadMutation, MarkAlertAsReadMutationVariables,
} from '@michi/types';

export const GET_UNREAD_ALERTS: TypedDocumentNode<GetUnreadAlertsQuery, GetUnreadAlertsQueryVariables> = gql`
  query GetUnreadAlerts($storeId: ID) {
    unreadAlerts(storeId: $storeId) {
      id
      productId
      type
      message
      isRead
      severity
      createdAt
    }
  }
`;

export const MARK_ALERT_AS_READ: TypedDocumentNode<MarkAlertAsReadMutation, MarkAlertAsReadMutationVariables> = gql`
  mutation MarkAlertAsRead($alertId: ID!) {
    markAlertAsRead(alertId: $alertId)
  }
`;
