/**
 * GraphQL Queries
 */
import { gql } from '@apollo/client';

export const GET_ME = gql`
  query GetMe {
    me {
      id
      email
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
