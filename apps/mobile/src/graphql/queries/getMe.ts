import { gql } from '@apollo/client';
import type { GetMeQuery, GetMeQueryVariables } from '@michi/types';
import type { TypedDocumentNode } from '@apollo/client';

export const GET_ME: TypedDocumentNode<GetMeQuery, GetMeQueryVariables> = gql`
  query GetMe {
    me {
      id
      email
      firstName
      lastName
      currentOrganizationId
      createdAt
      organizations {
        organizationId
        role
        organization {
          id
          name
          slug
        }
      }
    }
  }
`;
