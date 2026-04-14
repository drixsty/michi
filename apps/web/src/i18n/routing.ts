import { defineRouting } from 'next-intl/routing';

export const routing = defineRouting({
  locales: ['fr', 'en'],
  defaultLocale: 'fr',
  // Default locale (fr) has no prefix: /dashboard
  // Other locales are prefixed: /en/dashboard
  localePrefix: 'as-needed',
});
