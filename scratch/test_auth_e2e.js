const { ApolloClient, InMemoryCache, gql, createHttpLink } = require('@apollo/client/core');
const fetch = require('cross-fetch');

const client = new ApolloClient({
  link: createHttpLink({ uri: 'http://localhost:8000/graphql', fetch }),
  cache: new InMemoryCache(),
});

const LOGIN = gql`
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      token
      user {
        email
        currentOrganizationId
      }
    }
  }
`;

const GET_ME = gql`
  query GetMe {
    me {
      id
      email
      currentOrganizationId
      organizations {
        organizationId
        role
      }
    }
  }
`;

async function runTest() {
  console.log("--- Starting Auth E2E Test ---");
  try {
    // 1. Login
    console.log("Attempting Login...");
    const loginRes = await client.mutate({
      mutation: LOGIN,
      variables: {
        input: { email: "dev@michi.com", password: "michi123" }
      }
    });
    
    const token = loginRes.data.login.token;
    console.log("Login Success! Token received.");
    
    // 2. Try to use the token for GET_ME
    console.log("Attempting GET_ME with token...");
    // We need a new client or a modified link to send the token
    const authClient = new ApolloClient({
      link: createHttpLink({ 
        uri: 'http://localhost:8000/graphql', 
        fetch,
        headers: { authorization: `Bearer ${token}` }
      }),
      cache: new InMemoryCache(),
    });

    const meRes = await authClient.query({ query: GET_ME });
    console.log("GET_ME Success!");
    console.log("User Email:", meRes.data.me.email);
    console.log("Active Org:", meRes.data.me.currentOrganizationId);
    
    console.log("--- Auth Flow VALIDATED ---");
  } catch (err) {
    console.error("--- Auth Flow FAILED ---");
    if (err.graphQLErrors) {
      err.graphQLErrors.forEach(e => console.error("GraphQL Error:", e.message, e.extensions?.code));
    } else {
      console.error(err);
    }
    process.exit(1);
  }
}

runTest();
