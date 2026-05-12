'use client';

import React from 'react';
import { useTranslations } from 'next-intl';
import { LegalTemplate } from '@/components/LegalTemplate';

export default function PrivacyPage() {
  const t = useTranslations('Legal.privacy');
  const sections = t.raw('sections');

  return (
    <LegalTemplate title={t('title')} subtitle={t('subtitle')}>
      <div className="space-y-8 text-muted-foreground leading-relaxed">
        {Object.entries(sections).map(([key, section]: [string, any]) => (
          <section key={key}>
            <h2 className="text-xl font-bold text-foreground mb-4">{section.title}</h2>
            <p dangerouslySetInnerHTML={{ __html: section.content }} />
            {section.items && (
              <ul className="list-disc pl-5 space-y-2 mt-4">
                {section.items.map((item: string, i: number) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
    </LegalTemplate>
  );
}
