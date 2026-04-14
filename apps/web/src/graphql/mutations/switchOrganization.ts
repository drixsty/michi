import { gql } from '@apollo/client';

export const SWITCH_ORGANIZATION = gql`
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
