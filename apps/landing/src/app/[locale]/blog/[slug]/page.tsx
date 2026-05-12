'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { ArrowLeft, Calendar, User, Share2 } from 'lucide-react';

export default function BlogPost({ params: { slug } }: { params: { slug: string } }) {
  const t = useTranslations('Blog');

  return (
    <div className="pb-20 px-6">
      <article className="max-w-2xl mx-auto pt-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <a href="/blog" className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-primary transition-colors mb-8 text-xs font-medium">
            <ArrowLeft className="w-3.5 h-3.5" /> {t('backToAcademy')}
          </a>

          <h1 className="text-[1.7rem] font-bold mb-4 tracking-tight leading-[1.2] text-foreground">
            {t(`posts.${slug}.title` as any)}
          </h1>

          <div className="flex flex-wrap items-center gap-4 text-muted-foreground text-xs mb-8 pb-8 border-b border-border">
            <span className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> {t(`posts.${slug}.date` as any)}</span>
            <span className="flex items-center gap-1.5"><User className="w-3.5 h-3.5" /> {t('teamName')}</span>
            <button 
              onClick={() => {
                const url = window.location.href;
                if (navigator.share) {
                  navigator.share({
                    title: document.title,
                    url: url
                  }).catch(console.error);
                } else {
                  navigator.clipboard.writeText(url);
                  alert("Lien copié dans le presse-papier !");
                }
              }}
              className="flex items-center gap-1.5 hover:text-primary transition-colors ml-auto"
            >
              <Share2 className="w-3.5 h-3.5" /> {t('share')}
            </button>
          </div>

          <div className="text-muted-foreground leading-relaxed space-y-5 text-sm">
            <p className="text-sm font-medium text-foreground">
              {t(`posts.${slug}.description` as any)}
            </p>

            {t.rich(`posts.${slug}.content` as any, {
              h2Inner: (chunks) => <h2 className="text-base font-semibold text-foreground mt-8 mb-3">{chunks}</h2>,
              h3Inner: (chunks) => <h3 className="text-sm font-semibold text-foreground mt-6 mb-2">{chunks}</h3>,
              pInner: (chunks) => <p className="mb-4">{chunks}</p>
            })}

            <div className="bg-secondary border border-border p-5 rounded-lg mt-8">
              <h2 className="text-sm font-semibold text-foreground mb-2">{t('summary')}</h2>
              <p className="text-xs text-muted-foreground leading-relaxed">{t('summaryContent')}</p>
            </div>
          </div>
        </motion.div>
      </article>

    </div>
  );
}
