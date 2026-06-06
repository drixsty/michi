'use client';

import React, { useState, useEffect } from 'react';
import { useMutation, gql } from '@apollo/client';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Lock, Mail, Server } from 'lucide-react';

const LOGIN_MUTATION = gql`
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      token
      user {
        id
        email
        firstName
        lastName
      }
    }
  }
`;

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // S'assurer de rediriger si déjà connecté
  useEffect(() => {
    if (localStorage.getItem('michi_token')) {
      router.push('/');
    }
  }, [router]);

  const [login, { loading }] = useMutation(LOGIN_MUTATION, {
    onCompleted: (data) => {
      const token = data?.login?.token;
      if (token) {
        localStorage.setItem('michi_token', token);
        toast.success('Authentification réussie !');
        router.push('/');
      }
    },
    onError: (error) => {
      toast.error(error.message || 'Identifiants invalides ou droits insuffisants');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }
    login({
      variables: {
        input: {
          email,
          password,
        },
      },
    });
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-4">
      {/* Background ambient glowing circles */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl -z-10 animate-glow"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl -z-10 animate-glow" style={{ animationDelay: '1s' }}></div>

      <div className="w-full max-w-md p-8 rounded-2xl glass-card text-slate-100 flex flex-col items-center">
        {/* Console Logo/Header */}
        <div className="flex items-center space-x-2 bg-indigo-500/10 border border-indigo-500/20 px-4 py-1.5 rounded-full mb-6 text-indigo-400 text-sm font-semibold tracking-wide">
          <Server className="w-4 h-4" />
          <span>PORTAL SUPPORT PROD</span>
        </div>

        <h1 className="text-3xl font-bold tracking-tight text-center bg-gradient-to-r from-indigo-300 to-purple-400 bg-clip-text text-transparent mb-2">
          Michi 道 Support
        </h1>
        <p className="text-slate-400 text-sm text-center mb-8">
          Console d'opérations et de diagnostic technique.
        </p>

        <form onSubmit={handleSubmit} className="w-full space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300 flex items-center space-x-2">
              <Mail className="w-4 h-4 text-indigo-400" />
              <span>Adresse Email Support</span>
            </label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="agent@michi.com"
                className="w-full bg-slate-900/60 border border-slate-700/50 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300 flex items-center space-x-2">
              <Lock className="w-4 h-4 text-indigo-400" />
              <span>Mot de passe</span>
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              className="w-full bg-slate-900/60 border border-slate-700/50 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-xl transition-all hover:shadow-lg hover:shadow-indigo-500/20 active:scale-95 disabled:opacity-50 disabled:scale-100 flex items-center justify-center space-x-2 mt-4"
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            ) : (
              <span>Se Connecter à la Console</span>
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-xs text-slate-500">
          Accès restreint. Toutes les connexions et actions sont auditées.
        </div>
      </div>
    </div>
  );
}
