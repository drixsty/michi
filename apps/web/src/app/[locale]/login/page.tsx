'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, Lock, Mail, Info, KeyRound, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMutation } from '@apollo/client';
import { LOGIN, VERIFY_2FA } from '@/graphql/mutations/login';
import { GoogleLogin } from '@react-oauth/google';
import { GOOGLE_LOGIN } from '@/graphql/mutations/googleLogin';
import { useTranslations } from 'next-intl';
import { PasswordInput } from '@/components/ui/PasswordInput';

export default function LoginPage() {
  const t = useTranslations('auth.login');
  const tBrand = useTranslations('brand');
  const t2fa = useTranslations('profile.twoFactor');

  const router = useRouter();
  const [email, setEmail] = useState('dev@michi.com');
  const [password, setPassword] = useState('password123');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [isUsingRecovery, setIsUsingRecovery] = useState(false);

  const [login, { loading: loginLoading }] = useMutation(LOGIN, {
    onCompleted: (data: any) => {
      if (data.login.mfaRequired) {
        setMfaToken(data.login.mfaToken);
        setErrorMessage(null);
      } else {
        localStorage.setItem('michi_token', data.login.token);
        router.push('/dashboard');
      }
    },
    onError: (err) => {
      console.error('Login Error:', err);
      setErrorMessage(t('errorCredentials'));
    },
  });

  const [verify2fa, { loading: verifyLoading }] = useMutation(VERIFY_2FA, {
    onCompleted: (data) => {
      localStorage.setItem('michi_token', data.verify2fa.token);
      router.push('/dashboard');
    },
    onError: (err) => {
      setErrorMessage(err.message);
    }
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
    if (mfaToken) {
      await verify2fa({ variables: { mfaToken, code: mfaCode } });
    } else {
      await login({ variables: { input: { email, password } } });
    }
  };

  const toggleRecovery = () => {
    setIsUsingRecovery(!isUsingRecovery);
    setMfaCode('');
    setErrorMessage(null);
  };

  const isBtnLoading = loginLoading || googleLoading || verifyLoading;

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
                <AlertCircle className="h-3.5 w-3.5" />
                {errorMessage}
              </div>
            )}

            {!mfaToken ? (
              <>
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

                <PasswordInput
                  label={t('passwordLabel')}
                  placeholder={t('passwordPlaceholder')}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />

                <div className="flex justify-end">
                  <Link 
                    href="/forgot-password" 
                    className="text-[11px] font-bold text-primary hover:underline transition-all"
                  >
                    {t('forgotPasswordLink')}
                  </Link>
                </div>
              </>
            ) : (
              <div className="space-y-4 py-2 animate-in zoom-in-95 duration-300">
                <div className={cn(
                  "p-3 rounded-lg border text-center transition-colors",
                  isUsingRecovery ? "bg-amber-50 border-amber-100" : "bg-primary/5 border-primary/10"
                )}>
                  <h3 className={cn("text-sm font-bold mb-1", isUsingRecovery ? "text-amber-700" : "text-primary")}>
                    {isUsingRecovery ? "Code de secours" : t2fa('enterCodeTitle')}
                  </h3>
                  <p className="text-[10px] text-muted-foreground">
                    {isUsingRecovery 
                      ? "Saisissez l'un de vos 10 codes de récupération de 8 caractères." 
                      : t2fa('enterCodeDesc')}
                  </p>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-bold text-foreground/60 ml-1">
                    {isUsingRecovery ? "Code de récupération" : t2fa('verifyCodeLabel')}
                  </label>
                  <div className="relative group">
                    {isUsingRecovery ? (
                       <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-amber-500/60 group-focus-within:text-amber-600 transition-colors" />
                    ) : (
                       <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
                    )}
                    <input
                      type="text"
                      maxLength={isUsingRecovery ? 8 : 6}
                      placeholder={isUsingRecovery ? "XXXXXXXX" : "000000"}
                      required
                      autoFocus
                      value={mfaCode}
                      onChange={(e) => setMfaCode(e.target.value.toUpperCase().replace(isUsingRecovery ? /[^A-Z0-9]/g : /\D/g, ''))}
                      className={cn(
                        "w-full h-12 bg-background border rounded-md px-4 text-center text-xl font-mono tracking-[0.5em] outline-none transition-all",
                        isUsingRecovery 
                          ? "border-amber-200 focus:ring-4 focus:ring-amber-500/5 focus:border-amber-500/30" 
                          : "border-border focus:ring-4 focus:ring-primary/5 focus:border-primary/20"
                      )}
                    />
                  </div>
                </div>
                
                <div className="flex flex-col gap-2">
                  <button 
                    type="button"
                    onClick={toggleRecovery}
                    className="text-[11px] font-bold text-primary hover:text-primary/80 transition-all w-full text-center"
                  >
                    {isUsingRecovery ? "Utiliser l'application TOTP" : "Utiliser un code de secours"}
                  </button>
                  <button 
                    type="button"
                    onClick={() => {
                      setMfaToken(null);
                      setIsUsingRecovery(false);
                    }}
                    className="text-[11px] font-medium text-muted-foreground hover:text-foreground underline transition-all w-full text-center"
                  >
                    {useTranslations('common')('cancel')}
                  </button>
                </div>
              </div>
            )}

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
          {!mfaToken && (
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
                    theme="outline"
                    shape="rectangular"
                    text="signin_with"
                  />
                </div>
              </div>
            </div>
          )}

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

        <div className="relative z-10 w-full max-lg space-y-8 animate-in slide-in-from-right-8 duration-1000">
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
