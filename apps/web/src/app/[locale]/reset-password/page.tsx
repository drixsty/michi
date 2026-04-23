'use client';

import React, { useState, useEffect } from 'react';
import { Lock, ArrowRight, CheckCircle2, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import { gql, useMutation } from '@apollo/client';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams, useRouter } from 'next/navigation';
import { PasswordInput } from '@/components/ui/PasswordInput';

const RESET_PASSWORD = gql`
  mutation ResetPassword($input: ResetPasswordInput!) {
    resetPassword(input: $input)
  }
`;

export default function ResetPasswordPage() {
  const t = useTranslations('auth.resetPassword');
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [resetPassword, { loading }] = useMutation(RESET_PASSWORD, {
    onCompleted: (data) => {
      if (data.resetPassword) {
        setSubmitted(true);
        // Redirection auto après 3 secondes
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      } else {
        setError(t('errorInvalid'));
      }
    },
    onError: (err) => {
      setError(err.message || t('errorGeneric'));
    }
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError(t('errorMismatch'));
      return;
    }

    if (!token) {
      setError(t('errorInvalid'));
      return;
    }

    try {
      await resetPassword({ 
        variables: { 
          input: { 
            token, 
            newPassword: password 
          } 
        } 
      });
    } catch (err) {}
  };

  if (!token && !submitted) {
    return (
      <div className="min-h-screen bg-[#FDFDFF] flex items-center justify-center p-6">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <h1 className="text-2xl font-bold text-slate-900">{t('errorInvalid')}</h1>
          <Link href="/login" className="text-primary font-bold hover:underline">
            {t('backToLogin')}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFDFF] flex items-center justify-center p-6 selection:bg-primary/10">
      <div className="w-full max-w-[400px] space-y-8">
        <div className="flex flex-col items-center text-center space-y-4">
          <Link href="/login" className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-2xl shadow-2xl shadow-primary/20 hover:scale-105 transition-transform">
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
              <form onSubmit={handleSubmit} className="space-y-4 bg-white p-8 rounded-3xl border border-slate-100 shadow-xl shadow-slate-200/50">
                {error && (
                  <div className="p-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs font-bold flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                  </div>
                )}

                <PasswordInput
                  label={t('newPasswordLabel')}
                  placeholder="••••••••"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  minLength={8}
                />

                <PasswordInput
                  label={t('confirmPasswordLabel')}
                  placeholder="••••••••"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  minLength={8}
                />

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full h-12 bg-slate-900 text-white rounded-xl text-sm font-bold transition-all hover:bg-slate-800 active:scale-[0.98] flex items-center justify-center gap-2 shadow-xl shadow-slate-900/10 mt-2"
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
              </form>
            </motion.div>
          ) : (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white p-10 rounded-3xl border border-slate-100 shadow-xl shadow-slate-200/50 text-center space-y-6"
            >
              <div className="w-16 h-16 bg-green-50 text-green-500 rounded-full flex items-center justify-center mx-auto shadow-inner">
                <CheckCircle2 className="h-8 w-8" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-slate-900">{t('successTitle')}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  {t('successMessage')}
                </p>
              </div>
              <p className="text-xs text-slate-400 animate-pulse">
                Redirection vers la page de connexion...
              </p>
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
          &copy; 2026 Michi 道 — Secure Password Reset
        </p>
      </div>
    </div>
  );
}
