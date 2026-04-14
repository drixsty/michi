/**
 * Apollo Client Configuration
 * GraphQL client pour communiquer avec le backend
 */
import { ApolloClient, InMemoryCache, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8000/graphql',
});

// Auth link : Ajoute le token JWT et l'ID de l'organisation à chaque requête
const authLink = setContext((_, { headers }) => {
  if (typeof window === 'undefined') return { headers };
  
  const token = localStorage.getItem('michi_token');
  const orgRaw = localStorage.getItem('michi_current_org');
  let orgId = '';
  
  if (orgRaw) {
    try {
      orgId = JSON.parse(orgRaw).id;
    } catch (e) {}
  }
  
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
      'michi-org-id': orgId || '',
      'apollo-require-preflight': 'true',
    },
  };
});

// Error link : Gestion des erreurs GraphQL
const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, extensions }) => {
      const code = extensions?.code;
      
      // Si UNAUTHENTICATED, rediriger vers login
      if (code === 'UNAUTHENTICATED' && typeof window !== 'undefined') {
        console.warn("[Apollo] Session expired, clearing local data.");
        localStorage.removeItem('michi_token');
        localStorage.removeItem('michi_current_org');
        
        // Éviter la boucle de rechargement si on est déjà sur /login
        if (window.location.pathname !== '/login' && window.location.pathname !== '/onboarding') {
          window.location.href = '/login';
        }
      }
    });
  }
  
  if (networkError) {
    console.error(`[Network error]: ${networkError}`);
  }
});

// Apollo Client instance
export const apolloClient = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
});
