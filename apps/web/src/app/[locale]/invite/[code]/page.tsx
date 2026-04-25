'use client';

import React, { useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useQuery, useMutation } from '@apollo/client';
import { GET_INVITATION_PREVIEW, ACCEPT_INVITATION } from '@/graphql/mutations/invitation';
import { Loader2, ArrowRight, Building2, Mail, UserPlus, AlertCircle } from 'lucide-react';
import Link from 'next/link';

export default function InvitePreviewPage() {
  const router = useRouter();
  const params = useParams();
  const code = params.code as string;

  const { data, loading, error } = useQuery(GET_INVITATION_PREVIEW, {
    variables: { code },
    skip: !code,
    fetchPolicy: 'network-only'
  });

  const [acceptInvitation, { loading: accepting }] = useMutation(ACCEPT_INVITATION, {
    onCompleted: () => {
      router.push('/dashboard');
    },
    onError: (err) => {
      console.error('Accept invitation error:', err);
    }
  });

  const isAuthenticated = typeof window !== 'undefined' && !!localStorage.getItem('michi_token');

  const handleAccept = () => {
    if (isAuthenticated) {
      acceptInvitation({ variables: { code } });
    } else {
      router.push(`/register?invite=${code}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (error || !data?.invitationPreview) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-lg border border-red-100 shadow-sm text-center max-w-md w-full">
          <div className="w-12 h-12 bg-red-50 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Invitation invalide</h2>
          <p className="text-sm text-slate-500 mb-6">
            Ce lien d'invitation est invalide, a expiré ou a déjà été utilisé.
          </p>
          <Link href="/login" className="text-primary font-bold hover:underline text-sm">
            Retourner à la connexion
          </Link>
        </div>
      </div>
    );
  }

  const invite = data.invitationPreview;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white rounded-lg border shadow-lg overflow-hidden max-w-md w-full animate-in zoom-in-95 duration-500">
        <div className="p-8 text-center space-y-6">
          
          <div className="flex justify-center -space-x-2">
            <div className="w-16 h-16 rounded-full bg-slate-100 border-4 border-white flex items-center justify-center text-slate-400 z-10 shadow-sm">
              <UserPlus className="w-6 h-6" />
            </div>
            <div className="w-16 h-16 rounded-full bg-primary/10 border-4 border-white flex items-center justify-center text-primary z-0 shadow-sm">
              <Building2 className="w-6 h-6" />
            </div>
          </div>

          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Vous avez été invité(e)</h1>
            <p className="text-slate-500 mt-2 text-sm leading-relaxed">
              <span className="font-bold text-slate-700">{invite.invitedByName}</span> vous a invité(e) à rejoindre l'organisation <span className="font-bold text-slate-700">{invite.organizationName}</span> sur Michi.
            </p>
          </div>

          <div className="bg-slate-50 rounded-lg p-4 text-left border border-slate-100">
            <div className="flex items-center gap-3 text-sm text-slate-600 mb-2">
              <Mail className="w-4 h-4 text-slate-400" />
              <span>Invité par : {invite.invitedByEmail}</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <Building2 className="w-4 h-4 text-slate-400" />
              <span>Rôle : <span className="font-bold capitalize">{invite.role.toLowerCase()}</span></span>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={handleAccept}
              disabled={accepting}
              className="w-full h-12 bg-slate-900 text-white rounded-lg text-sm font-bold hover:bg-slate-800 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
            >
              {accepting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  {isAuthenticated ? "Rejoindre l'organisation" : "Créer un compte pour rejoindre"}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {!isAuthenticated && (
            <p className="text-xs text-slate-500 font-medium">
              Déjà un compte ?{' '}
              <Link href={`/login?invite=${code}`} className="text-primary hover:underline">
                Se connecter
              </Link>
            </p>
          )}

        </div>
      </div>
    </div>
  );
}
