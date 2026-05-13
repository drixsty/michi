'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { Shield, Lock, FileText, ArrowLeft } from 'lucide-react';

interface LegalTemplateProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export const LegalTemplate = ({ title, subtitle, children }: LegalTemplateProps) => {
  return (
    <div className="overflow-x-hidden min-h-screen">
      {/* Hero */}
      <section className="max-w-4xl mx-auto pt-24 pb-12 px-4 sm:px-6">
        <motion.div 
          initial={{ opacity: 0, y: 16 }} 
          animate={{ opacity: 1, y: 0 }} 
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <a
            href="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-primary transition-colors mb-8 min-h-[44px]"
          >
            <ArrowLeft className="w-3 h-3" />
            Back to Home
          </a>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-4 tracking-tight text-foreground">
            {title}
          </h1>
          <p className="text-muted-foreground text-base sm:text-lg max-w-lg mx-auto leading-relaxed">
            {subtitle}
          </p>
        </motion.div>
      </section>

      {/* Content */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 pb-24">
        <div className="bg-card/50 backdrop-blur-sm border border-border rounded-3xl p-5 sm:p-8 md:p-12 shadow-sm">
          <div className="prose prose-sm prose-invert max-w-none">
            {children}
          </div>
        </div>
      </section>
    </div>
  );
};
