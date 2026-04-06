import { gql } from '@apollo/client';

export const GET_UNREAD_ALERTS = gql`
  query GetUnreadAlerts {
    unreadAlerts {
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

export const MARK_ALERT_AS_READ = gql`
  mutation MarkAlertAsRead($alertId: ID!) {
    markAlertAsRead(alertId: $alertId)
  }
`;
