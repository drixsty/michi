'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { ArrowRight, BookOpen, Calendar, User } from 'lucide-react';

const BlogCard = ({ category, title, date, author, slug }: { category: string, title: string, date: string, author: string, slug: string }) => (
  <a href={`/blog/${slug}`} className="block group">
    <div className="bg-card rounded-lg overflow-hidden border border-border hover:border-primary/30 transition-colors">
      <div className="h-36 bg-secondary flex items-center justify-center">
        <BookOpen className="w-7 h-7 text-muted-foreground/20" />
      </div>
      <div className="p-5">
        <div className="text-primary text-[10px] font-bold uppercase tracking-widest mb-2">{category}</div>
        <h3 className="text-sm font-semibold text-foreground mb-3 group-hover:text-primary transition-colors leading-snug">{title}</h3>
        <div className="flex items-center justify-between text-muted-foreground text-xs">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {date}</span>
            <span className="flex items-center gap-1"><User className="w-3 h-3" /> {author}</span>
          </div>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </div>
      </div>
    </div>
  </a>
);

export default function BlogContent() {
  const t = useTranslations('Blog');

  const posts = [
    { slug: 'stockouts-2026', category: t('categories.strategy'), title: t('posts.stockouts-2026.title'), date: t('posts.stockouts-2026.date'), author: t('teamName') },
    { slug: 'ai-demand-planning', category: t('categories.forecasting'), title: t('posts.ai-demand-planning.title'), date: t('posts.ai-demand-planning.date'), author: t('posts.ai-demand-planning.author') },
    { slug: 'multi-channel-guide', category: t('categories.guides'), title: t('posts.multi-channel-guide.title'), date: t('posts.multi-channel-guide.date'), author: t('posts.multi-channel-guide.author') },
  ];

  return (
    <div className="overflow-x-hidden min-h-screen">

      {/* Hero */}
      <section className="max-w-3xl mx-auto pt-28 pb-14 px-6 text-center">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h1 className="text-[1.9rem] md:text-[2.6rem] font-bold mb-3 tracking-tight leading-[1.2] text-foreground">
            {t.rich('hero.title', {
              spanInner: (chunks) => <span className="text-gradient-purple">{chunks}</span>
            })}
          </h1>
          <p className="text-muted-foreground text-[0.9rem] max-w-lg mx-auto leading-relaxed">
            {t('hero.subtitle')}
          </p>
        </motion.div>
      </section>

      {/* Posts */}
      <section className="max-w-5xl mx-auto px-6 pb-20 border-t border-border pt-12">
        <div className="grid md:grid-cols-3 gap-4">
          {posts.map((post, idx) => (
            <BlogCard key={idx} {...post} />
          ))}
        </div>
      </section>

    </div>
  );
}
