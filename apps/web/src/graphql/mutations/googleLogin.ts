import { gql } from '@apollo/client';

export const GOOGLE_LOGIN = gql`
  mutation GoogleLogin($input: GoogleLoginInput!) {
    googleLogin(input: $input) {
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
