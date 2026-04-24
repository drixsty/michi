import { gql, TypedDocumentNode } from '@apollo/client';
import type { LoginMutation, LoginMutationVariables } from '@michi/types';

export const LOGIN = gql`
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      token
      mfaRequired
      mfaToken
      user {
        id
        email
        currentOrganizationId
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
  }
`;

export const VERIFY_2FA = gql`
  mutation Verify2FA($mfaToken: String!, $code: String!) {
    verify2fa(mfaToken: $mfaToken, code: $code) {
      token
      user {
        id
        email
        currentOrganizationId
      }
    }
  }
`;
