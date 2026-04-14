import { gql, TypedDocumentNode } from '@apollo/client';
import type {
  GetSourcesQuery, GetSourcesQueryVariables,
  ToggleSourceMutation, ToggleSourceMutationVariables,
} from '@michi/types';

export const GET_SOURCES: TypedDocumentNode<GetSourcesQuery, GetSourcesQueryVariables> = gql`
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

export const TOGGLE_SOURCE: TypedDocumentNode<ToggleSourceMutation, ToggleSourceMutationVariables> = gql`
  mutation ToggleSource($platform: String!, $connected: Boolean!, $storeId: ID) {
    toggleSource(platform: $platform, connected: $connected, storeId: $storeId) {
      id
      connected
      platform
    }
  }
`;
