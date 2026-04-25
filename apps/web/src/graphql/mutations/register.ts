import { gql, TypedDocumentNode } from '@apollo/client';
import type { RegisterMutation, RegisterMutationVariables } from '@michi/types';

export const REGISTER: TypedDocumentNode<RegisterMutation, RegisterMutationVariables> = gql`
  mutation Register($input: RegisterInput!) {
    register(input: $input) {
      token
      user {
        id
        email
        firstName
        lastName
        currentOrganizationId
        hasOrganization
        onboardingCompleted
      }
    }
  }
`;
