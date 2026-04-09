'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Chrome, Ship, ArrowRight, Lock, Mail, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useMutation } from '@apollo/client';
import { LOGIN } from '@/graphql/mutations/login';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('dev@michi.com');
  const [password, setPassword] = useState('password123');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [login, { loading: mutationLoading }] = useMutation(LOGIN, {
    onCompleted: (data) => {
      const { token } = data.login;
      localStorage.setItem('michi_token', token);
      router.push('/dashboard');
    },
    onError: (err) => {
      console.error("Login Error:", err);
      setErrorMessage("Identifiants incorrects ou problème serveur.");
    }
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    try {
      await login({
        variables: {
          input: { email, password }
        }
      });
    } catch (err) {
      // Handled in onError
    }
  };

  const isBtnLoading = mutationLoading;

  return (
    <div className="min-h-screen bg-background flex selection:bg-primary/10 flex-col lg:flex-row shadow-sm">
      {/* Left Column: Login Form */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center p-6 lg:p-8 animate-in fade-in duration-700">
        <div className="w-full max-w-sm space-y-8">
          
          {/* Header Section */}
          <div className="flex flex-col items-start space-y-4">
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-xl shadow-lg shadow-primary/20 animate-in zoom-in duration-500">
              道
            </div>
            <div className="space-y-1">
              <h1 className="text-3xl font-bold tracking-tight text-foreground">Bon retour</h1>
              <p className="text-sm text-muted-foreground">
                Connectez-vous pour gérer vos stocks omnicanaux.
              </p>
            </div>
          </div>

          {/* Form Section */}
          <form onSubmit={handleLogin} className="space-y-4">
            {errorMessage && (
              <div className="p-3 rounded-md bg-red-50 border border-red-100 text-red-600 text-xs font-medium flex items-center gap-2 animate-in fade-in slide-in-from-top-1">
                <Info className="h-4 w-4" />
                {errorMessage}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground ml-1">Adresse email</label>
              <div className="relative group">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
                <input
                  type="email"
                  placeholder="nom@exemple.com"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-11 pl-10 pr-4 rounded-md border bg-background text-sm transition-all focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary border-border"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground ml-1">Mot de passe</label>
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
                <input
                  type="password"
                  placeholder="••••••••"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-11 pl-10 pr-4 rounded-md border bg-background text-sm transition-all focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary border-border"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isBtnLoading}
              className={cn(
                "w-full h-11 bg-foreground text-background rounded-md text-sm font-semibold transition-all hover:opacity-90 active:scale-[0.98] flex items-center justify-center gap-2 mt-4",
                isBtnLoading && "opacity-70 cursor-not-allowed"
              )}
            >
              {isBtnLoading ? (
                <div className="h-4 w-4 border-2 border-background/30 border-t-background rounded-full animate-spin" />
              ) : (
                <>
                  <span>Se connecter</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* OAuth Section */}
          <div className="space-y-5">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-background px-2 text-muted-foreground font-medium">Ou continuer avec</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="relative group">
                <button 
                  disabled 
                  className="w-full flex h-11 items-center justify-center gap-2 rounded-md border bg-muted/50 px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed border-border"
                >
                  <Chrome className="h-4 w-4" />
                  Google
                </button>
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-foreground text-background text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                  Bientôt disponible
                </div>
              </div>

              <div className="relative group">
                <button 
                  disabled 
                  className="w-full flex h-11 items-center justify-center gap-2 rounded-md border bg-muted/50 px-4 py-2 text-sm font-medium opacity-50 cursor-not-allowed border-border"
                >
                  <Ship className="h-4 w-4" />
                  Shopify
                </button>
                <div className="absolute -top-10 left-1/2 -translate-x-1/2 px-2 py-1 bg-foreground text-background text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                  Bientôt disponible
                </div>
              </div>
            </div>
          </div>

          {/* Footer info */}
          <p className="text-center text-[12px] text-muted-foreground px-8 leading-relaxed">
            En continuant, vous acceptez nos <span className="underline underline-offset-4 cursor-pointer hover:text-foreground transition-colors">conditions d&apos;utilisation</span>.
          </p>
        </div>
      </div>

      {/* Right Column: Brand Immersive Section */}
      <div className="hidden lg:flex lg:w-1/2 bg-[#0A0A0A] relative overflow-hidden items-center justify-center p-8 lg:p-12">
        {/* Abstract Background Decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-transparent opacity-50" />
        <div className="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[60%] h-[60%] rounded-full bg-primary/5 blur-[120px]" />
        
        <div className="relative z-10 w-full max-w-lg space-y-8 animate-in slide-in-from-right-8 duration-1000">
          <div className="flex items-center gap-4">
             <div className="h-[1px] w-12 bg-primary/50" />
             <span className="text-primary text-xs font-bold tracking-[0.2em]">Michi 道 UI 2.0</span>
          </div>
          
          <h2 className="text-4xl xl:text-5xl font-bold text-white leading-tight">
            La précision au cœur de votre <span className="text-primary italic">croissance</span>.
          </h2>
          
          <p className="text-lg text-white/50 leading-relaxed font-light">
            Automatisez vos prévisions de stocks et réduisez vos ruptures de 40% grâce à notre moteur IA omnicanal.
          </p>

          <div className="pt-8 grid grid-cols-2 gap-8 border-t border-white/10">
            <div className="space-y-1">
              <span className="text-2xl font-bold text-white">99%</span>
              <p className="text-xs text-white/40 tracking-widest font-semibold">Fiabilité IA</p>
            </div>
            <div className="space-y-1">
              <span className="text-2xl font-bold text-white">40%</span>
              <p className="text-xs text-white/40 tracking-widest font-semibold">Ruptures en moins</p>
            </div>
          </div>
        </div>

        {/* Floating Brand Elements */}
        <div className="absolute bottom-12 right-12 opacity-20 rotate-12 scale-150">
          <div className="text-[200px] font-bold text-white select-none">道</div>
        </div>
      </div>
    </div>
  );
}
