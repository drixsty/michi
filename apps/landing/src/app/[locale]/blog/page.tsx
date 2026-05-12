import { setRequestLocale } from 'next-intl/server';
import BlogContent from '@/app/[locale]/blog/BlogContent';

export default function BlogPage({ params: { locale } }: { params: { locale: string } }) {
  setRequestLocale(locale);

  return <BlogContent />;
}
