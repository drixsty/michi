import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  overwrite: true,
  schema: './schema.graphql',
  documents: '../../apps/web/src/graphql/**/*.ts', // On typte les opérations du web
  generates: {
    './src/graphql.ts': {
      plugins: ['typescript', 'typescript-operations'],
      config: {
        skipTypename: false,
        withHooks: false,
        pureMagicComment: true,
      },
    },
  },
};

export default config;
