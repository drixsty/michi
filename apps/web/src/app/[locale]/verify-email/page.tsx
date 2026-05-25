'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useMutation, useQuery } from '@apollo/client';
import { Mail, CheckCircle2, XCircle, Loader2, ArrowLeft, Send } from 'lucide-react';
import { VERIFY_EMAIL } from '@/graphql/mutations/verifyEmail';
import { RESEND_VERIFICATION_EMAIL } from '@/graphql/mutations/resendVerificationEmail';
import { GET_ME } from '@/graphql/queries/getMe';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';
import Link from 'next/link';

export default function VerifyEmailPage() {
  const t = useTranslations('verifyEmail');
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  
  const [status, setStatus] = useState<'pending' | 'success' | 'error' | 'idle'>(token ? 'pending' : 'idle');
  const [cooldown, setCooldown] = useState(0);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Fetch current user email for resend
  const { data: userData } = useQuery(GET_ME);
  const userEmail = userData?.me?.email;

  const [verifyEmail] = useMutation(VERIFY_EMAIL, {
    onCompleted: (data) => {
      if (data.verifyEmail) {
        setStatus('success');
        setTimeout(() => {
          router.push('/pricing');
        }, 3000);
      } else {
        setStatus('error');
      }
    },
    onError: () => {
      setStatus('error');
    }
  });

  const [resendEmail, { loading: resending }] = useMutation(RESEND_VERIFICATION_EMAIL, {
    onCompleted: (data) => {
      if (data.resendVerificationEmail) {
        setResendSuccess(true);
        setCooldown(60); // 60s cooldown
        setTimeout(() => setResendSuccess(false), 5000);
      }
    },
    onError: (err) => {
      console.error('Resend error:', err);
    }
  });

  useEffect(() => {
    // Si l'utilisateur est déjà vérifié, on considère que c'est un succès immédiat
    if (userData?.me?.emailVerifiedAt && status !== 'success') {
      setStatus('success');
      setTimeout(() => {
        router.push('/pricing');
      }, 2000);
      return;
    }

    if (token && status === 'pending') {
      verifyEmail({ variables: { token } });
    }
  }, [token, verifyEmail, status, userData]);

  // Countdown timer for resend button
  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  const handleResend = () => {
    if (userEmail && cooldown === 0) {
      resendEmail({ variables: { email: userEmail } });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 font-sans">
      <div className="max-w-md w-full bg-white rounded-lg border border-slate-200 p-10 text-center">
        <div className="mb-8 flex justify-center">
          <div className={cn(
            "w-20 h-20 rounded-lg flex items-center justify-center transition-all duration-500",
            status === 'success' ? "bg-green-50 text-green-600 scale-110" :
            status === 'error' ? "bg-red-50 text-red-600" :
            "bg-primary/5 text-primary"
          )}>
            {status === 'success' ? <CheckCircle2 className="w-10 h-10" /> :
             status === 'error' ? <XCircle className="w-10 h-10" /> :
             status === 'pending' ? <Loader2 className="w-10 h-10 animate-spin" /> :
             <Mail className="w-10 h-10" />}
          </div>
        </div>

        <h1 className="text-2xl font-bold text-slate-900 mb-2 tracking-tight">
          {status === 'success' ? t('success') : 
           status === 'error' ? t('error') : 
           t('title')}
        </h1>

        <p className="text-slate-500 mb-8 leading-relaxed">
          {status === 'idle' ? t('description') :
           status === 'pending' ? t('verifying') :
           status === 'success' ? t('redirecting') :
           t('errorDescription')}
        </p>

        {(status === 'idle' || status === 'error') && (
          <div className="space-y-4">
             <div className="p-4 bg-slate-50 rounded-lg text-[13px] text-slate-600 leading-relaxed border border-slate-100">
               {t('checkSpam')}
             </div>
             
             <button 
               onClick={handleResend}
               disabled={cooldown > 0 || resending || !userEmail}
               className={cn(
                 "w-full py-3 rounded-lg font-bold transition-all text-sm tracking-wide flex items-center justify-center gap-2",
                 cooldown > 0 || !userEmail
                   ? "bg-slate-100 text-slate-400 cursor-not-allowed" 
                   : resendSuccess 
                     ? "bg-green-500 text-white" 
                     : "bg-primary text-white hover:bg-primary/90"
               )}
             >
               {resending ? (
                 <Loader2 className="w-4 h-4 animate-spin" />
               ) : resendSuccess ? (
                 <>
                   <CheckCircle2 className="w-4 h-4" />
                   {t('resendSuccess')}
                 </>
               ) : cooldown > 0 ? (
                 t('resendCooldown', { seconds: cooldown })
               ) : (
                 <>
                   <Send className="w-4 h-4" />
                   {t('resend')}
                 </>
               )}
             </button>

             {userEmail && (
               <p className="text-[11px] text-slate-400 italic">
                 Sent to <span className="font-semibold text-slate-500">{userEmail}</span>
               </p>
             )}
          </div>
        )}

        {(status === 'error' || status === 'idle') && (
          <Link 
            href="/login"
            className="mt-8 inline-flex items-center text-sm font-bold text-slate-400 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('backToLogin')}
          </Link>
        )}
      </div>
    </div>
  );
}
