import { gql, TypedDocumentNode } from '@apollo/client';
import type { SwitchOrganizationMutation, SwitchOrganizationMutationVariables } from '@michi/types';

export const SWITCH_ORGANIZATION: TypedDocumentNode<SwitchOrganizationMutation, SwitchOrganizationMutationVariables> = gql`
  mutation SwitchOrganization($organizationId: ID!) {
    switchOrganization(organizationId: $organizationId) {
      token
      user {
        id
        email
        currentOrganizationId
      }
    }
  }
`;
