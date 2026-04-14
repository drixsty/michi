const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

// Monorepo workspace root
const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);

// Allow Metro to resolve modules from the monorepo root
config.watchFolders = [workspaceRoot];

config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
];

// Ensure Metro can resolve packages/* from the monorepo
config.resolver.extraNodeModules = {
  '@michi/types': path.resolve(workspaceRoot, 'packages/types/src'),
};

module.exports = config;
