import createMiddleware from 'next-intl/middleware';
// Triggering a reload of the middleware to refresh translations

export default createMiddleware({
  locales: ['en', 'fr'],
  defaultLocale: 'en'
});

export const config = {
  matcher: ['/((?!_next).*)']
};
