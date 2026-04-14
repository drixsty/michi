'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Chrome, ArrowRight, Lock, Mail, Info, User, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMutation } from '@apollo/client';
import { REGISTER } from '@/graphql/mutations/register';
import { GOOGLE_LOGIN } from '@/graphql/mutations/googleLogin';
import { GoogleLogin } from '@react-oauth/google';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function RegisterPage() {
  const router = useRouter();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [register, { loading: mutationLoading }] = useMutation(REGISTER, {
    onCompleted: (data) => {
      const { token } = data.register;
      localStorage.setItem('michi_token', token);
      router.push('/dashboard?onboarding=true'); // Flag to trigger onboarding
    },
    onError: (err) => {
      console.error("Register Error:", err);
      setErrorMessage(err.message || "Erreur lors de l'inscription.");
    }
  });

  const [googleLogin, { loading: googleLoading }] = useMutation(GOOGLE_LOGIN, {
    onCompleted: (data) => {
      const { token } = data.googleLogin;
      localStorage.setItem('michi_token', token);
      router.push('/dashboard');
    },
    onError: (err) => {
      console.error("Google Auth Error:", err);
      setErrorMessage("Échec de l'authentification Google.");
    }
  });

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    try {
      await register({
        variables: {
          input: { email, password, firstName, lastName }
        }
      });
    } catch (err) {}
  };

  return (
    <div className="min-h-screen bg-background flex selection:bg-primary/10 flex-col lg:flex-row">
      {/* Left Decoration (Dynamic & Professional) */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#0A0A0A] relative overflow-hidden items-center justify-center p-12">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent opacity-40" />
        
        <div className="relative z-10 w-full max-w-lg space-y-12">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="flex items-center gap-4">
               <div className="h-[1px] w-12 bg-primary/50" />
               <span className="text-primary text-[10px] font-bold tracking-[0.3em] uppercase">Join the path</span>
            </div>
            <h2 className="text-5xl font-bold text-white leading-tight tracking-tight">
              Prenez le contrôle de votre <span className="text-primary italic">inventaire</span>.
            </h2>
            <p className="text-lg text-white/50 leading-relaxed font-light">
              Rejoignez des centaines de marchands qui optimisent leur supply chain avec Michi 道.
            </p>
          </motion.div>

          {/* Value Props */}
          <div className="space-y-6">
            {[
              "Prévisions IA Ultra-Précises",
              "Gestion Multi-Boutiques Centralisée",
              "Alertes Rupture en Temps Réel"
            ].map((text, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 + i * 0.1 }}
                className="flex items-center gap-4 text-white/70"
              >
                <CheckCircle2 className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium">{text}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Content: Registration Form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center p-3 lg:p-4 animate-in fade-in duration-700">
        <div className="w-full max-w-[320px] space-y-4">
          
          <div className="flex flex-col items-center text-center space-y-1">
            <Link href="/" className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-lg shadow-xl shadow-primary/20 mb-1 hover:scale-105 transition-transform">
              道
            </Link>
            <h1 className="text-xl font-bold tracking-tight text-foreground">Créer votre compte</h1>
            <p className="text-[11px] text-muted-foreground font-medium">
              Essai gratuit de 14 jours.
            </p>
          </div>

          <div className="space-y-3">
            {/* Google Signup */}
            <div className="flex justify-center">
              <div className="w-full max-w-[240px]">
                <GoogleLogin 
                  onSuccess={(credentialResponse) => {
                    googleLogin({ variables: { input: { idToken: credentialResponse.credential } } });
                  }}
                  onError={() => setErrorMessage("Erreur Google Auth")}
                  useOneTap
                  theme="outline"
                  shape="rectangular"
                  text="signup_with"
                />
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-background px-3 text-muted-foreground font-medium italic">Ou avec votre email</span>
              </div>
            </div>

            <form onSubmit={handleRegister} className="space-y-1.5">
              {errorMessage && (
                <div className="p-2 rounded-lg bg-red-50 border border-red-100 text-red-600 text-[10px] font-bold flex items-center gap-2 animate-in shake duration-500">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {errorMessage}
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-0.5">
                  <label className="text-[10px] font-bold text-slate-500 ml-1">Prénom</label>
                  <div className="relative group">
                    <User className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/30 group-focus-within:text-primary transition-colors" />
                    <input
                      type="text"
                      placeholder="Jean"
                      required
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="w-full h-11 pl-8 pr-3 rounded-lg border bg-slate-50/50 text-[13px] transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-transparent focus:bg-white"
                    />
                  </div>
                </div>
                <div className="space-y-0.5">
                  <label className="text-[10px] font-bold text-slate-500 ml-1">Nom</label>
                  <div className="relative group">
                    <User className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/30 group-focus-within:text-primary transition-colors" />
                    <input
                      type="text"
                      placeholder="Dupont"
                      required
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="w-full h-11 pl-8 pr-3 rounded-lg border bg-slate-50/50 text-[13px] transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-transparent focus:bg-white"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-0.5">
                <label className="text-[10px] font-bold text-slate-500 ml-1">Email professionnel</label>
                <div className="relative group">
                  <Mail className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/30 group-focus-within:text-primary transition-colors" />
                  <input
                    type="email"
                    placeholder="email@entreprise.com"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full h-11 pl-8 pr-3 rounded-lg border bg-slate-50/50 text-[13px] transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-transparent focus:bg-white"
                  />
                </div>
              </div>

              <div className="space-y-0.5">
                <label className="text-[10px] font-bold text-slate-500 ml-1">Mot de passe</label>
                <div className="relative group">
                  <Lock className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/30 group-focus-within:text-primary transition-colors" />
                  <input
                    type="password"
                    placeholder="••••••••"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-11 pl-8 pr-3 rounded-lg border bg-slate-50/50 text-[13px] transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-transparent focus:bg-white"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={mutationLoading}
                className={cn(
                  "w-full h-11 bg-slate-900 text-white rounded-lg text-xs font-bold transition-all hover:bg-slate-800 active:scale-[0.98] flex items-center justify-center gap-2 mt-2 shadow-xl shadow-slate-900/10",
                  mutationLoading && "opacity-70 cursor-not-allowed"
                )}
              >
                {mutationLoading ? (
                  <div className="h-3 w-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Créer mon compte</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </>
                )}
              </button>
            </form>
          </div>

          <p className="text-center text-[11px] text-muted-foreground font-medium">
            Déjà un compte ?{' '}
            <Link href="/login" className="text-primary font-bold hover:underline">
              Se connecter
            </Link>
          </p>

          <p className="text-center text-[9px] text-slate-400 leading-tight max-w-[240px] mx-auto italic">
            En continuant, vous acceptez nos <span className="underline cursor-pointer">conditions</span> et notre <span className="underline cursor-pointer">confidentialité</span>.
          </p>
        </div>
      </div>
    </div>
  );
}

function AlertCircle(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
  );
}
