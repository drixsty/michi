import { gql } from '@apollo/client';

export const GET_SOURCES = gql`
  query GetSources {
    sources {
      id
      name
      platform
      connected
      lastSyncAt
      healthStatus
      organizationId
    }
  }
`;

export const TOGGLE_SOURCE = gql`
  mutation ToggleSource($platform: String!, $connected: Boolean!, $storeId: ID) {
    toggleSource(platform: $platform, connected: $connected, storeId: $storeId) {
      id
      connected
      platform
    }
  }
`;
