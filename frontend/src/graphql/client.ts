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

// Auth link : Ajoute le token JWT à chaque requête
const authLink = setContext((_, { headers }) => {
  // Récupérer le token depuis localStorage
  const token = typeof window !== 'undefined' ? localStorage.getItem('michi_token') : null;
  
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    },
  };
});

// Error link : Gestion des erreurs GraphQL
const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, extensions }) => {
      const code = extensions?.code;
      
      console.error(`[GraphQL error]: ${message}, Code: ${code}`);
      
      // Si UNAUTHENTICATED, rediriger vers login
      if (code === 'UNAUTHENTICATED' && typeof window !== 'undefined') {
        localStorage.removeItem('michi_token');
        window.location.href = '/login';
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
