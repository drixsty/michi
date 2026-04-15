'use client';

import React, { useState, useMemo } from 'react';
import { useMutation, gql } from '@apollo/client';
import {
  UserPlus,
  Mail,
  Shield,
  CheckCircle2,
  AlertCircle,
  AlertTriangle
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { SidePanel } from '../ui/SidePanel';

const INVITE_MEMBER = gql`
  mutation InviteMember($email: String!, $role: String!) {
    inviteMember(email: $email, role: $role) {
      id
      email
    }
  }
`;

interface Member {
  userId: string;
  user: { email: string } | null;
}

interface PendingInvitation {
  id: string;
  email: string;
}

interface InviteMemberPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  existingMembers?: Member[];
  pendingInvitations?: PendingInvitation[];
}

const ROLES = [
  { id: 'ADMIN', label: 'Administrateur', description: "Accès total à l'organisation et aux paramètres." },
  { id: 'MANAGER', label: 'Gestionnaire', description: 'Gère les fournisseurs et l\'inventaire.' },
  { id: 'VIEWER', label: 'Lecteur', description: 'Consultation uniquement.' },
];

type ConflictType = 'already_member' | 'already_invited' | null;

export function InviteMemberPanel({
  isOpen,
  onClose,
  onSuccess,
  existingMembers = [],
  pendingInvitations = [],
}: InviteMemberPanelProps) {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('VIEWER');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const t = useTranslations('organization.invite');
  const tRoles = useTranslations('organization.roles');

  const ROLES = [
    { id: 'ADMIN', label: tRoles('admin'), description: tRoles('adminDesc') },
    { id: 'MANAGER', label: tRoles('manager'), description: tRoles('managerDesc') },
    { id: 'VIEWER', label: tRoles('viewer'), description: tRoles('viewerDesc') },
  ];

  // Validation préventive en temps réel
  const conflict = useMemo<ConflictType>(() => {
    if (!email) return null;
    const normalizedEmail = email.trim().toLowerCase();
    if (existingMembers.some((m) => m.user?.email?.toLowerCase() === normalizedEmail)) {
      return 'already_member';
    }
    if (pendingInvitations.some((i) => i.email.toLowerCase() === normalizedEmail)) {
      return 'already_invited';
    }
    return null;
  }, [email, existingMembers, pendingInvitations]);

  const isBlocked = !!conflict;

  const [inviteMember] = useMutation(INVITE_MEMBER, {
    refetchQueries: ['GetOrgData'],
    awaitRefetchQueries: true,
    onCompleted: () => {
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 1500);
    },
    onError: (err) => {
      setServerError(err.message);
      setIsSubmitting(false);
    }
  });

  const handleClose = () => {
    setEmail('');
    setRole('VIEWER');
    setServerError(null);
    setSuccess(false);
    setIsSubmitting(false);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || isBlocked) return;
    setIsSubmitting(true);
    setServerError(null);
    await inviteMember({ variables: { email: email.trim(), role } });
  };

  return (
    <SidePanel
      isOpen={isOpen}
      onClose={handleClose}
      title={t('title')}
      subtitle={t('subtitle')}
      footer={
        <div className="flex gap-3">
          <button
            onClick={handleClose}
            className="flex-1 py-3 px-4 bg-white border border-slate-200 text-slate-600 rounded-lg text-[10px] font-bold hover:bg-slate-50 focus:ring-0 focus:outline-none transition-colors"
          >
            {useTranslations('common')('cancel')}
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !email || success || isBlocked}
            className={cn(
              "flex-[2] py-3 px-4 rounded-lg text-[10px] font-bold transition-all flex items-center justify-center gap-2 focus:ring-0 focus:outline-none",
              success
                ? "bg-emerald-500 text-white"
                : isBlocked
                ? "bg-slate-100 text-slate-400 cursor-not-allowed"
                : "bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-100 disabled:text-slate-400"
            )}
          >
            {isSubmitting ? t('sending') : success ? (
              <><CheckCircle2 className="h-3.5 w-3.5" /> {t('success')}</>
            ) : (
              <><UserPlus className="h-3.5 w-3.5" /> {t('send')}</>
            )}
          </button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="p-4 space-y-6">
        {/* Email Input */}
        <div className="space-y-2">
          <label className="text-[10px] font-bold text-slate-400 flex items-center gap-2">
            <Mail className="h-3 w-3" />
            {t('emailLabel')}
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setServerError(null); }}
            placeholder="exemple@michi.com"
            className={cn(
              "w-full h-11 px-4 bg-slate-100/50 border rounded-lg text-xs transition-all focus:bg-white focus:ring-4 focus:ring-primary/5 focus:ring-0 focus:outline-none placeholder:text-muted-foreground/50 font-medium text-slate-900",
              conflict === 'already_member'
                ? "border-red-200 bg-red-50/30 focus:border-red-200"
                : conflict === 'already_invited'
                ? "border-amber-200 bg-amber-50/30 focus:border-amber-200"
                : "border-transparent focus:border-primary/20"
            )}
            disabled={isSubmitting || success}
          />

          {/* Avertissement inline — validation préventive */}
          {conflict === 'already_member' && (
            <div className="flex items-start gap-2 px-3 py-2 bg-red-50 border border-red-100 rounded-lg animate-in fade-in zoom-in duration-200">
              <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0 mt-0.5" />
              <p className="text-[9px] font-bold text-red-600 leading-relaxed">
                {t('alreadyMember')}
              </p>
            </div>
          )}
          {conflict === 'already_invited' && (
            <div className="flex items-start gap-2 px-3 py-2 bg-amber-50 border border-amber-100 rounded-lg animate-in fade-in zoom-in duration-200">
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500 shrink-0 mt-0.5" />
              <p className="text-[9px] font-bold text-amber-600 leading-relaxed">
                {t('alreadyInvited')}
              </p>
            </div>
          )}
        </div>

        {/* Role Selection */}
        <div className="space-y-3">
          <label className="text-[10px] font-bold text-slate-400 flex items-center gap-2">
            <Shield className="h-3 w-3" />
            {t('roleLabel')}
          </label>
          <div className="grid grid-cols-1 gap-2">
            {ROLES.map((r) => (
              <button
                key={r.id}
                type="button"
                onClick={() => setRole(r.id)}
                className={cn(
                  "p-3 rounded-lg border text-left transition-all group focus:ring-0 focus:outline-none",
                  role === r.id
                    ? "bg-primary/5 border-primary/20 ring-1 ring-primary/20"
                    : "bg-white border-slate-100 hover:border-slate-200"
                )}
                disabled={isSubmitting || success}
              >
                <div className="flex items-center justify-between mb-0.5">
                  <span className={cn(
                    "text-[10px] font-black",
                    role === r.id ? "text-primary" : "text-slate-700"
                  )}>
                    {r.label}
                  </span>
                  {role === r.id && <CheckCircle2 className="h-3.5 w-3.5 text-primary" />}
                </div>
                <p className="text-[9px] text-slate-400 font-medium leading-relaxed">
                  {r.description}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Erreur serveur (fallback) */}
        {serverError && (
          <div className="p-3 bg-red-50 border border-red-100 rounded-lg flex items-start gap-3 animate-in fade-in zoom-in duration-300">
            <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-[10px] font-bold text-red-700">{t('error')}</p>
              <p className="text-[9px] text-red-600 font-medium leading-relaxed">{serverError}</p>
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="p-3 bg-slate-50/50 rounded-lg border border-slate-100">
          <p className="text-[9px] text-slate-400 font-bold leading-relaxed">
            * {t('info')}
          </p>
        </div>
      </form>
    </SidePanel>
  );
}
