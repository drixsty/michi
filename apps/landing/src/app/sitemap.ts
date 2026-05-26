import { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://michi.app';
  const locales = ['en', 'fr'];

  const staticPages = [
    { path: '', priority: 1.0, changeFrequency: 'weekly' as const },
    { path: '/features/forecasting', priority: 0.9, changeFrequency: 'weekly' as const },
    { path: '/features/replenishment', priority: 0.9, changeFrequency: 'weekly' as const },
    { path: '/features/unified-inventory', priority: 0.9, changeFrequency: 'weekly' as const },
    { path: '/integrations/shopify', priority: 0.9, changeFrequency: 'weekly' as const },
    { path: '/integrations/amazon', priority: 0.9, changeFrequency: 'weekly' as const },
    { path: '/integrations/woocommerce', priority: 0.9, changeFrequency: 'weekly' as const },
    { path: '/pricing', priority: 0.8, changeFrequency: 'monthly' as const },
    { path: '/blog', priority: 0.8, changeFrequency: 'weekly' as const },
    { path: '/about', priority: 0.7, changeFrequency: 'monthly' as const },
    { path: '/legal', priority: 0.3, changeFrequency: 'yearly' as const },
    { path: '/privacy', priority: 0.3, changeFrequency: 'yearly' as const },
    { path: '/terms', priority: 0.3, changeFrequency: 'yearly' as const },
  ];

  const blogPosts = [
    'stockouts-2026',
    'ai-demand-planning',
    'multi-channel-guide',
  ];

  const sitemapEntries: MetadataRoute.Sitemap = [];

  locales.forEach((locale) => {
    staticPages.forEach(({ path, priority, changeFrequency }) => {
      sitemapEntries.push({
        url: `${baseUrl}/${locale}${path}`,
        lastModified: new Date(),
        changeFrequency,
        priority,
      });
    });

    blogPosts.forEach((slug) => {
      sitemapEntries.push({
        url: `${baseUrl}/${locale}/blog/${slug}`,
        lastModified: new Date(),
        changeFrequency: 'monthly',
        priority: 0.6,
      });
    });
  });

  return sitemapEntries;
}
