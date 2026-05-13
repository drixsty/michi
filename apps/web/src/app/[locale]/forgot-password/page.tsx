'use client';

import React, { useState } from 'react';
import { Mail, ArrowRight, CheckCircle2, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { gql, useMutation } from '@apollo/client';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { motion, AnimatePresence } from 'framer-motion';

const FORGOT_PASSWORD = gql`
  mutation ForgotPassword($input: RequestPasswordResetInput!) {
    forgotPassword(input: $input)
  }
`;

export default function ForgotPasswordPage() {
  const t = useTranslations('auth.forgotPassword');
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [forgotPassword, { loading }] = useMutation(FORGOT_PASSWORD, {
    onCompleted: () => {
      setSubmitted(true);
    },
    onError: (err) => {
      setError(err.message || t('error'));
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await forgotPassword({ variables: { input: { email } } });
    } catch (err) {}
  };

  return (
    <div className="min-h-screen bg-[#FDFDFF] flex items-center justify-center p-6 selection:bg-primary/10">
      <div className="w-full max-w-[400px] space-y-8">
        <div className="flex flex-col items-center text-center space-y-4">
          <Link href="/login" className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-2xl hover:scale-105 transition-transform">
            道
          </Link>
          <div className="space-y-2">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">{t('title')}</h1>
            <p className="text-slate-500 font-medium">
              {submitted ? t('successTitle') : t('subtitle')}
            </p>
          </div>
        </div>

        <AnimatePresence mode="wait">
          {!submitted ? (
            <motion.div
              key="form"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              <form onSubmit={handleSubmit} className="space-y-4 bg-white p-5 sm:p-8 rounded-3xl border border-slate-100">
                {error && (
                  <div className="p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs font-bold flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                  </div>
                )}

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-slate-400 tracking-wider ml-1">{t('emailLabel')}</label>
                  <div className="relative group">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-300 group-focus-within:text-primary transition-colors" />
                    <input
                      type="email"
                      placeholder={t('emailPlaceholder')}
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full h-12 pl-12 pr-4 rounded-xl border border-slate-100 bg-slate-50/50 text-sm transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 focus:bg-white"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-slate-900 text-white rounded-xl text-sm font-bold transition-all hover:bg-slate-800 active:scale-[0.98] flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <span>{t('submitButton')}</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>

                <Link href="/login" className="flex items-center justify-center gap-2 text-xs font-bold text-slate-400 hover:text-primary transition-colors min-h-[44px]">
                  <ArrowLeft className="h-3 w-3" />
                  {t('backToLogin')}
                </Link>
              </form>
            </motion.div>
          ) : (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white p-10 rounded-3xl border border-slate-100 text-center space-y-6"
            >
              <div className="w-16 h-16 bg-green-50 text-green-500 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-slate-900">{t('successTitle')}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  {t('successMessage')}
                </p>
              </div>
              <Link
                href="/login"
                className="inline-flex items-center gap-2 text-sm font-bold text-primary hover:underline"
              >
                <ArrowLeft className="h-4 w-4" />
                {t('backToLogin')}
              </Link>
            </motion.div>
          )}
        </AnimatePresence>

        <p className="text-center text-[11px] text-slate-400 font-medium">
          &copy; 2026 Michi 道 — Secure account recovery
        </p>
      </div>
    </div>
  );
}
