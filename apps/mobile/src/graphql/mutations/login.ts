import { gql } from '@apollo/client';
import type { LoginMutation, LoginMutationVariables } from '@michi/types';
import type { TypedDocumentNode } from '@apollo/client';

export const LOGIN: TypedDocumentNode<LoginMutation, LoginMutationVariables> = gql`
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      token
      user {
        id
        email
        firstName
        lastName
        currentOrganizationId
      }
    }
  }
`;
