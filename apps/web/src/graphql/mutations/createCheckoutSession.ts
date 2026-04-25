import { gql } from '@apollo/client';

export const CREATE_CHECKOUT_SESSION = gql`
  mutation CreateCheckoutSession($plan: String!, $successUrl: String!, $cancelUrl: String!) {
    createCheckoutSession(plan: $plan, successUrl: $successUrl, cancelUrl: $cancelUrl)
  }
`;
