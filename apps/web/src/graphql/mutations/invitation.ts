import { gql } from '@apollo/client';

export const ACCEPT_INVITATION = gql`
  mutation AcceptInvitation($code: String!) {
    acceptInvitation(code: $code)
  }
`;

export const GET_INVITATION_PREVIEW = gql`
  query GetInvitationPreview($code: String!) {
    invitationPreview(code: $code) {
      organizationName
      role
      invitedByName
      invitedByEmail
      expiresAt
    }
  }
`;
