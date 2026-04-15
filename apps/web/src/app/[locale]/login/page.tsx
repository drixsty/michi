'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, Lock, Mail, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMutation } from '@apollo/client';
import { LOGIN } from '@/graphql/mutations/login';
import { GoogleLogin } from '@react-oauth/google';
import { GOOGLE_LOGIN } from '@/graphql/mutations/googleLogin';
import { useTranslations } from 'next-intl';

export default function LoginPage() {
  const t = useTranslations('auth.login');
  const tBrand = useTranslations('brand');

  const router = useRouter();
  const [email, setEmail] = useState('dev@michi.com');
  const [password, setPassword] = useState('password123');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [login, { loading: loginLoading }] = useMutation(LOGIN, {
    onCompleted: (data) => {
      localStorage.setItem('michi_token', data.login.token);
      router.push('/dashboard');
    },
    onError: (err) => {
      console.error('Login Error:', err);
      setErrorMessage(t('errorCredentials'));
    },
  });

  const [googleLogin, { loading: googleLoading }] = useMutation(GOOGLE_LOGIN, {
    onCompleted: (data) => {
      localStorage.setItem('michi_token', data.googleLogin.token);
      router.push('/dashboard');
    },
    onError: (err) => {
      console.error('Google Login Error:', err);
      setErrorMessage(t('errorGoogle'));
    },
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    await login({ variables: { input: { email, password } } });
  };

  const isBtnLoading = loginLoading || googleLoading;

  return (
    <div className="min-h-screen bg-background flex selection:bg-primary/10 flex-col lg:flex-row shadow-sm">
      {/* Left Column: Login Form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center p-4 lg:p-4 animate-in fade-in duration-700">
        <div className="w-full max-w-[320px] space-y-4">

          {/* Header */}
          <div className="flex flex-col items-start space-y-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-base shadow-lg shadow-primary/20 animate-in zoom-in duration-500">
              道
            </div>
            <div className="space-y-0.5">
              <h1 className="text-xl font-bold tracking-tight text-foreground">{t('title')}</h1>
              <p className="text-[13px] text-muted-foreground font-medium">{t('subtitle')}</p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-2.5">
            {errorMessage && (
              <div className="p-2.5 rounded-md bg-red-50 border border-red-100 text-red-600 text-[10px] font-medium flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
                <Info className="h-3.5 w-3.5" />
                {errorMessage}
              </div>
            )}
            <div className="space-y-1">
              <label className="text-[11px] font-bold text-foreground/60 ml-1">{t('emailLabel')}</label>
              <div className="relative group">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
                <input
                  type="email"
                  placeholder={t('emailPlaceholder')}
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-11 pl-10 pr-4 rounded-md border bg-background text-sm transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-border"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-foreground/60 ml-1">{t('passwordLabel')}</label>
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
                <input
                  type="password"
                  placeholder={t('passwordPlaceholder')}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-11 pl-10 pr-4 rounded-md border bg-background text-sm transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-border"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isBtnLoading}
              className={cn(
                'w-full h-11 bg-foreground text-background rounded-md text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98] flex items-center justify-center gap-2 mt-2',
                isBtnLoading && 'opacity-70 cursor-not-allowed'
              )}
            >
              {isBtnLoading ? (
                <div className="h-4 w-4 border-2 border-background/30 border-t-background rounded-full animate-spin" />
              ) : (
                <>
                  <span>{t('submitButton')}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </form>

          {/* OAuth */}
          <div className="space-y-3">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-[10px]">
                <span className="bg-background px-2 text-muted-foreground font-medium italic">{t('orContinueWith')}</span>
              </div>
            </div>
            <div className="flex justify-center">
              <div className="w-full max-w-[280px]">
                <GoogleLogin
                  onSuccess={(credentialResponse) => {
                    googleLogin({ variables: { input: { idToken: credentialResponse.credential } } });
                  }}
                  onError={() => setErrorMessage(t('errorGoogleAuth'))}
                  useOneTap
                  theme="outline"
                  shape="rectangular"
                  text="signin_with"
                />
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center space-y-2">
            <p className="text-[11px] font-medium text-muted-foreground">
              {t('noAccount')}{' '}
              <Link href="/register" className="text-primary font-bold hover:underline">
                {t('registerLink')}
              </Link>
            </p>
            <p className="text-[9px] text-muted-foreground/50 px-8 leading-tight italic">
              {t('terms').split(t('termsLink'))[0]}
              <span className="underline underline-offset-4 cursor-pointer hover:text-foreground">{t('termsLink')}</span>
              {t('terms').split(t('termsLink'))[1]}
            </p>
          </div>
        </div>
      </div>

      {/* Right Column: Brand */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#0A0A0A] relative overflow-hidden items-center justify-center p-8 lg:p-12">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-transparent opacity-50" />
        <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-primary/5 blur-[120px]" />

        <div className="relative z-10 w-full max-w-lg space-y-8 animate-in slide-in-from-right-8 duration-1000">
          <div className="flex items-center gap-4">
            <div className="h-[1px] w-12 bg-primary/50" />
            <span className="text-primary text-xs font-bold tracking-[0.2em]">{tBrand('version')}</span>
          </div>
          <h2 className="text-4xl xl:text-5xl font-bold text-white leading-tight">
            {tBrand('tagline').split('.')[0]}
            <span className="text-primary italic"> {tBrand('tagline').split(' ').slice(-1)[0].replace('.', '')}</span>.
          </h2>
          <p className="text-lg text-white/50 leading-relaxed font-light">{tBrand('description')}</p>
          <div className="pt-8 grid grid-cols-2 gap-8 border-t border-white/10">
            <div className="space-y-1">
              <span className="text-2xl font-bold text-white">99%</span>
              <p className="text-xs text-white/40 tracking-widest font-semibold">{tBrand('stats.accuracy')}</p>
            </div>
            <div className="space-y-1">
              <span className="text-2xl font-bold text-white">40%</span>
              <p className="text-xs text-white/40 tracking-widest font-semibold">{tBrand('stats.stockoutReduction')}</p>
            </div>
          </div>
        </div>

        <div className="absolute bottom-12 right-12 opacity-20 rotate-12 scale-150">
          <div className="text-[200px] font-bold text-white select-none">道</div>
        </div>
      </div>
    </div>
  );
}
