import { redirect } from 'next/navigation';

export default async function LocaleHomePage({ params }: { params: Promise<{ locale: string }> | { locale: string } }) {
  const resolvedParams = await params;
  const locale = resolvedParams?.locale || 'fr';
  redirect(`/${locale}/dashboard`);
}
