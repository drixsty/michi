import {getRequestConfig} from 'next-intl/server';

export default getRequestConfig(async ({locale}) => {
  // Defensive check for locale
  const targetLocale = ['en', 'fr'].includes(locale) ? locale : 'en';

  return {
    locale: targetLocale,
    messages: (await import(`../messages/${targetLocale}.json`)).default
  };
});
