import { gql } from '@apollo/client';

export const GET_TEAM_DATA = gql`
  query GetTeamData {
    organizationMembers {
      organizationId
      userId
      role
      permissions
      user {
        id
        email
        firstName
        lastName
        createdAt
      }
    }
    pendingInvitations {
      id
      email
      role
      status
      code
      createdAt
      expiresAt
    }
    currentOrganization {
      id
      name
      plan
      subscriptionStatus
      settings
      stores {
        id
        name
        channel
      }
    }
    me {
      id
      isAdmin
    }
  }
`;

export const INVITE_MEMBER = gql`
  mutation InviteMember($email: String!, $role: String!) {
    inviteMember(email: $email, role: $role) {
      id
      email
      role
    }
  }
`;

export const REMOVE_MEMBER = gql`
  mutation RemoveMember($userId: ID!) {
    removeMember(userId: $userId)
  }
`;

export const UPDATE_MEMBER_ROLE = gql`
  mutation UpdateMemberRole($userId: ID!, $role: String!) {
    updateMemberRole(userId: $userId, role: $role)
  }
`;

export const DELETE_INVITATION = gql`
  mutation DeleteInvitation($invitationId: ID!) {
     deleteInvitation(invitationId: $invitationId)
  }
`;
