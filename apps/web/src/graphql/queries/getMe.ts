import { gql, TypedDocumentNode } from '@apollo/client';
import type { GetMeQuery, GetMeQueryVariables } from '@michi/types';

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
          onboardingCompleted
          onboardingStep
        }
      }
    }
  }
`;
