const withNextIntl = require('next-intl/plugin')(
  './src/i18n/request.ts'
);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@michi/ui"],
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'michi.app',
      },
    ],
  },
};

module.exports = withNextIntl(nextConfig);
