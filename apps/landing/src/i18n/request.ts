import {getRequestConfig} from 'next-intl/server';

export default getRequestConfig(async ({locale}) => {
  // next-intl guarantees locale is defined via middleware / generateStaticParams
  const safeLocale: string = locale ?? 'en';
  const targetLocale = ['en', 'fr'].includes(safeLocale) ? safeLocale : 'en';

  return {
    locale: targetLocale,
    messages: (await import(`../../messages/${targetLocale}.json`)).default
  };
});
