const createNextIntlPlugin = require('next-intl/plugin');

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  transpilePackages: ['@michi/assistant-ui'],

  // Environment Variables
  env: {
    NEXT_PUBLIC_GRAPHQL_URL: process.env.NEXT_PUBLIC_GRAPHQL_URL || 'http://localhost:8000/graphql',
    NEXT_PUBLIC_ENABLE_ASSISTANT_BETA: process.env.NEXT_PUBLIC_ENABLE_ASSISTANT_BETA || 'true',
    NEXT_PUBLIC_ASSISTANT_API_URL: process.env.NEXT_PUBLIC_ASSISTANT_API_URL || 'http://localhost:8001/graphql',
    NEXT_PUBLIC_MAIN_API_URL: process.env.NEXT_PUBLIC_MAIN_API_URL || 'http://localhost:8000/graphql',
  },

  // Image Optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    domains: ['cdn.michi.app'],
  },

  // Security Headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

module.exports = withNextIntl(nextConfig);
