import { setRequestLocale } from 'next-intl/server';
import LandingContent from './LandingContent';

export default function LandingPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);

  return <LandingContent />;
}
