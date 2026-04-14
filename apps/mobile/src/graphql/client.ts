/**
 * Apollo Client — apps/mobile
 * Persona #1 Lead Tech : configuration stateless, auth via SecureStore.
 */
import {
  ApolloClient,
  InMemoryCache,
  createHttpLink,
  from,
} from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import * as SecureStore from 'expo-secure-store';

const TOKEN_KEY = 'michi_token';

/** Lit le token JWT depuis SecureStore (async → hook setContext). */
async function getToken(): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(TOKEN_KEY);
  } catch {
    return null;
  }
}

/** Sauvegarde le token JWT dans SecureStore. */
export async function saveToken(token: string): Promise<void> {
  await SecureStore.setItemAsync(TOKEN_KEY, token);
}

/** Supprime le token JWT (logout). */
export async function clearToken(): Promise<void> {
  await SecureStore.deleteItemAsync(TOKEN_KEY);
}

const httpLink = createHttpLink({
  uri: process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/graphql',
});

const authLink = setContext(async (_, { headers }) => {
  const token = await getToken();
  return {
    headers: {
      ...headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  };
});

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    for (const { message, extensions } of graphQLErrors) {
      if (extensions?.code === 'UNAUTHENTICATED') {
        clearToken().catch(console.error);
      }
      console.warn('[GraphQL error]', message);
    }
  }
  if (networkError) {
    console.error('[Network error]', networkError);
  }
});

export const apolloClient = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: { fetchPolicy: 'cache-and-network' },
  },
});
