'use client';

import React, { useState, useMemo } from 'react';
import { useMutation, gql } from '@apollo/client';
import { 
  X, 
  Trash2, 
  ShieldAlert, 
  Ban, 
  CheckCircle2, 
  AlertCircle,
  Mail,
  Calendar,
  RefreshCw
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';

const UPDATE_MEMBER_PERMISSIONS = gql`
  mutation UpdateMemberPermissions($userId: ID!, $permissions: String!) {
    updateMemberPermissions(userId: $userId, permissions: $permissions) {
      userId
      permissions
    }
  }
`;

const REMOVE_MEMBER = gql`
  mutation RemoveMember($userId: ID!) {
    removeMember(userId: $userId)
  }
`;

const UPDATE_MEMBER_ROLE = gql`
  mutation UpdateMemberRole($userId: ID!, $role: String!) {
    updateMemberRole(userId: $userId, role: $role)
  }
`;

const TOGGLE_USER_STATUS = gql`
  mutation ToggleUserStatus($userId: ID!, $active: Boolean!) {
    toggleUserStatus(userId: $userId, active: $active)
  }
`;

const DELETE_INVITATION = gql`
  mutation DeleteInvitation($invitationId: ID!) {
     deleteInvitation(invitationId: $invitationId)
  }
`;


interface MemberDetailPanelProps {
  member?: any;
  invitation?: any;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  currentUserId?: string;
  currentUserRole?: string;
}

export function MemberDetailPanel({ 
  member, 
  invitation, 
  isOpen, 
  onClose, 
  onSuccess,
  currentUserRole = 'viewer'
}: MemberDetailPanelProps) {
  const [showConfirm, setShowConfirm] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const t = useTranslations('organization.memberDetail');
  const tRoles = useTranslations('organization.roles');
  const tPerms = useTranslations('organization.permissions');
  const tCommon = useTranslations('common');

  const PERMISSION_CATEGORIES = [
    {
      id: 'members',
      label: tPerms('team'),
      perms: [
        { id: 'members:view', label: tPerms('team_view') },
        { id: 'members:invite', label: tPerms('team_invite') },
        { id: 'members:remove', label: tPerms('team_remove') },
        { id: 'members:edit_role', label: tPerms('team_edit_role') },
      ]
    },
    {
      id: 'billing',
      label: tPerms('billing'),
      perms: [
        { id: 'billing:view', label: tPerms('billing_view') },
        { id: 'billing:manage', label: tPerms('billing_manage') },
      ]
    },
    {
      id: 'inventory',
      label: tPerms('inventory'),
      perms: [
        { id: 'inventory:view', label: tPerms('inventory_view') },
        { id: 'inventory:edit', label: tPerms('inventory_edit') },
        { id: 'stores:view', label: tPerms('stores_view') },
        { id: 'stores:manage', label: tPerms('stores_manage') },
      ]
    },
    {
      id: 'forecasting',
      label: tPerms('forecasting'),
      perms: [
        { id: 'forecasting:view', label: tPerms('forecasting_view') },
        { id: 'forecasting:run', label: tPerms('forecasting_run') },
      ]
    }
  ];

  const [removeMember, { loading: removing }] = useMutation(REMOVE_MEMBER);
  const [updateRole] = useMutation(UPDATE_MEMBER_ROLE);
  const [toggleStatus, { loading: togglingStatus }] = useMutation(TOGGLE_USER_STATUS);
  const [deleteInvitation, { loading: deletingInvite }] = useMutation(DELETE_INVITATION);
  const [updatePermissions, { loading: updatingPerms }] = useMutation(UPDATE_MEMBER_PERMISSIONS);

  const data = member || invitation;
  const isMember = !!member;
  
  // Permissions logic
  const currentPerms = useMemo(() => {
    try {
      if (!isMember || !member?.permissions) return {};
      // Handle both string and already parsed object (defensive)
      if (typeof member.permissions === 'string') {
        return JSON.parse(member.permissions);
      }
      return member.permissions || {};
    } catch (e) { 
      console.warn("[MemberDetailPanel] Permissions parse error:", e);
      return {}; 
    }
  }, [member?.permissions, isMember]);

  if (!isOpen || (!member && !invitation)) return null;

  const isAdmin = currentUserRole.toLowerCase() === 'admin';
  
  const email = isMember ? member.user.email : invitation.email;
  const firstName = isMember ? member.user.firstName : '';
  const lastName = isMember ? member.user.lastName : '';
  const name = (firstName || lastName) ? `${firstName} ${lastName}`.trim() : email.split('@')[0];
  const role = data.role.toLowerCase();
  
  const handleAction = async (action: string) => {
    try {
      if (action === 'remove') {
        const userId = isMember ? member.userId : null;
        if (userId) {
          await removeMember({ variables: { userId } });
          setSuccessMsg(t("successRemove"));
        }
      } else if (action === 'delete_invite') {
        await deleteInvitation({ variables: { id: invitation.id } });
        setSuccessMsg(t("successCancel"));
      } else if (action === 'ban') {
        await toggleStatus({ variables: { userId: member.userId, active: false } });
        setSuccessMsg(t("successBan"));
      } else if (action === 'unban') {
        await toggleStatus({ variables: { userId: member.userId, active: true } });
        setSuccessMsg(t("successUnban"));
      }
      
      setTimeout(() => {
        onSuccess();
        onClose();
        setShowConfirm(null);
        setSuccessMsg(null);
      }, 1500);
    } catch (err: any) {
      setErrorMsg(err.message);
      setTimeout(() => setErrorMsg(null), 3000);
    }
  };

  const handleChangeRole = async (newRole: string) => {
    try {
      await updateRole({ variables: { userId: member.userId, role: newRole } });
      setSuccessMsg(t('successRole', { role: tRoles(newRole.toLowerCase()) }));
      setTimeout(() => {
        onSuccess();
        setSuccessMsg(null);
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const handleTogglePermission = async (permId: string, currentVal: any) => {
    if (!isAdmin) return;
    
    // Toggle: undefined -> true -> false -> undefined (reset)
    let newVal: any;
    if (currentVal === undefined) newVal = true;
    else if (currentVal === true) newVal = false;
    else newVal = undefined;

    const newPerms = { ...currentPerms };
    if (newVal === undefined) {
      delete newPerms[permId];
    } else {
      newPerms[permId] = newVal;
    }

    try {
      await updatePermissions({
        variables: {
          userId: member.userId,
          permissions: JSON.stringify(newPerms)
        }
      });
      onSuccess();
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-900/10 backdrop-blur-[1px] z-[110] animate-in fade-in duration-300"
        onClick={onClose}
      />
      
      <div className="fixed top-0 right-0 h-full w-full max-w-[380px] bg-white border-l border-border z-[120] animate-in slide-in-from-right duration-300 flex flex-col">
        
        {/* Header (No Scroll) */}
        <div className="px-5 py-6 border-b border-border flex flex-col gap-4 relative shrink-0">
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 p-2 text-muted-foreground/40 hover:text-foreground transition-all rounded-lg hover:bg-muted"
          >
            <X className="h-4 w-4" />
          </button>

          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-lg bg-muted flex items-center justify-center text-muted-foreground text-2xl font-bold border border-border">
              {name.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0">
              <h2 className="text-lg font-semibold tracking-tight text-foreground truncate">{name}</h2>
              <p className="text-[13px] text-muted-foreground truncate">{email}</p>
            </div>
          </div>

          <div className="flex gap-2">
             <span className={cn(
               "text-[11px] font-bold px-2.5 py-1 rounded-md border tracking-tight",
                role === 'admin' ? "bg-red-50 text-red-600 border-red-100" :
                role === 'manager' ? "bg-amber-50 text-amber-600 border-amber-100" :
                "bg-emerald-50 text-emerald-600 border-emerald-100"
              )}>
                {tRoles(role)}
              </span>
              {isMember && (
                <span className="text-[11px] font-bold px-2.5 py-1 rounded-md border text-muted-foreground bg-muted/50 border-border tracking-tight">
                  {t('active')}
                </span>
              )}
              {!isMember && (
                <span className="text-[11px] font-bold px-2.5 py-1 rounded-md border text-amber-600 bg-amber-50 border-amber-100 tracking-tight">
                  {t('pending')}
                </span>
              )}
          </div>
        </div>

        {/* Content (No visible scrollbar) */}
        <div className="flex-1 overflow-y-auto p-5 space-y-8 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
          
          {(successMsg || errorMsg) && (
            <div className={cn(
              "p-3 rounded-lg border text-[13px] flex items-center gap-3 animate-in fade-in slide-in-from-top-1",
              successMsg ? "bg-emerald-50 border-emerald-100 text-emerald-700" : "bg-red-50 border-red-100 text-red-700"
            )}>
              {successMsg ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
              {successMsg || errorMsg}
            </div>
          )}

          <section className="space-y-3">
            <h3 className="text-[13px] font-semibold text-foreground px-1">{t('details')}</h3>
            <div className="space-y-3 bg-muted/10 rounded-lg p-4 border border-border">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-muted-foreground">
                  <Mail className="h-3.5 w-3.5" />
                  <span className="text-[13px] font-medium">{t('email')}</span>
                </div>
                <span className="text-[13px] font-semibold text-foreground truncate max-w-[180px]">{email}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-muted-foreground">
                  <Calendar className="h-3.5 w-3.5" />
                  <span className="text-[13px] font-medium">{isMember ? t('arrival') : t('inviteSent')}</span>
                </div>
                <span className="text-[13px] font-semibold text-foreground">
                  {new Date(data.createdAt).toLocaleDateString(t('locale') === 'fr' ? 'fr-FR' : 'en-US', { day: '2-digit', month: 'short', year: 'numeric' })}
                </span>
              </div>
            </div>
          </section>

          {isMember && (
            <section className="space-y-3">
              <h3 className="text-[13px] font-semibold text-foreground px-1 font-bold">{t('roleAccess')}</h3>
              <div className="grid grid-cols-1 gap-2">
                {['ADMIN', 'MANAGER', 'VIEWER'].map((r) => (
                  <button
                    key={r}
                    onClick={() => handleChangeRole(r)}
                    className={cn(
                      "flex items-center justify-between px-4 py-3 rounded-lg border transition-all text-left",
                      role === r.toLowerCase() 
                        ? "bg-primary/5 border-primary/20 ring-1 ring-primary/10" 
                        : "bg-white border-border hover:bg-muted"
                    )}
                  >
                    <div>
                      <p className={cn("text-[13px] font-semibold", role === r.toLowerCase() ? "text-primary" : "text-foreground")}>
                        {tRoles(r.toLowerCase())}
                      </p>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {tRoles(`${r.toLowerCase()}Desc`)}
                      </p>
                    </div>
                    {role === r.toLowerCase() && <CheckCircle2 className="h-4 w-4 text-primary" />}
                  </button>
                ))}
              </div>
            </section>
          )}

          {isMember && role !== 'admin' && isAdmin && (
            <section className="space-y-4 pt-6 border-t border-dashed border-border">
              <div className="flex items-center justify-between px-1">
                <h3 className="text-[13px] font-bold text-foreground">{t('permissions')}</h3>
                {updatingPerms && <RefreshCw className="h-3.5 w-3.5 animate-spin text-primary" />}
              </div>
              
              <div className="space-y-6">
                {PERMISSION_CATEGORIES.map((cat) => (
                  <div key={cat.id} className="space-y-2">
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest pl-1">{cat.label}</p>
                    <div className="bg-slate-50/50 rounded-xl border border-slate-100 p-1 divide-y divide-slate-100">
                       {cat.perms.map((p) => {
                         const override = currentPerms[p.id];
                         return (
                           <div key={p.id} className="flex items-center justify-between p-2.5">
                             <span className="text-[12px] font-medium text-slate-600">{p.label}</span>
                             <button
                               onClick={() => handleTogglePermission(p.id, override)}
                               className={cn(
                                 "w-12 h-6 rounded-full transition-all flex items-center px-1 border relative",
                                 override === true ? "bg-emerald-500 border-emerald-400" :
                                 override === false ? "bg-red-500 border-red-400" :
                                 "bg-slate-200 border-slate-300"
                               )}
                             >
                               <div className={cn(
                                 "w-4 h-4 rounded-full bg-white shadow-sm transition-all duration-200",
                                 override === true ? "translate-x-6" :
                                 override === false ? "translate-x-0" :
                                 "translate-x-3"
                               )} />
                             </button>
                           </div>
                         );
                       })}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground italic leading-relaxed text-center px-4">
                {t('permissionsLegend')}
              </p>
            </section>
          )}

          <section className="space-y-3 pt-6 border-t border-border">
            <h3 className="text-[13px] font-semibold text-red-500 px-1">{t('dangerZone')}</h3>
            
            <div className="space-y-2">
              {isMember ? (
                <>
                  <button 
                    onClick={() => setShowConfirm('remove')}
                    className="w-full h-11 flex items-center justify-between px-4 rounded-lg bg-red-50/50 border border-red-100 text-red-600 hover:bg-red-50 transition-all text-[13px] font-semibold"
                  >
                    <div className="flex items-center gap-3">
                      <Trash2 className="h-4 w-4" />
                      {t('remove')}
                    </div>
                  </button>

                  <button 
                    onClick={() => setShowConfirm('ban')}
                    className="w-full h-11 flex items-center justify-between px-4 rounded-lg bg-foreground text-background hover:opacity-90 transition-all text-[13px] font-semibold"
                  >
                    <div className="flex items-center gap-3">
                      <Ban className="h-4 w-4" />
                      {t('ban')}
                    </div>
                  </button>
                </>
              ) : (
                <button 
                  onClick={() => setShowConfirm('delete_invite')}
                  className="w-full h-11 flex items-center justify-between px-4 rounded-lg bg-red-50/50 border border-red-100 text-red-600 hover:bg-red-50 transition-all text-[13px] font-semibold"
                >
                  <div className="flex items-center gap-3">
                    <Trash2 className="h-4 w-4" />
                    {t('cancelInvite')}
                  </div>
                </button>
              )}
            </div>
          </section>
        </div>

        {/* Confirmation Modal */}
        {showConfirm && (
          <div className="absolute inset-0 bg-white/95 backdrop-blur-sm z-[130] flex flex-col items-center justify-center p-8 text-center animate-in fade-in duration-200">
            <div className="w-12 h-12 rounded-3xl bg-red-100 flex items-center justify-center text-red-600 mb-4">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <h4 className="text-lg font-bold text-foreground mb-2">{t('confirmTitle')}</h4>
            <p className="text-[13px] text-muted-foreground mb-8">
              {showConfirm === 'remove' ? t('confirmRemove') : 
               showConfirm === 'ban' ? t('confirmBan') :
               t('confirmCancel')}
            </p>
            <div className="flex flex-col w-full gap-2 px-10">
              <button 
                onClick={() => handleAction(showConfirm)}
                disabled={removing || deletingInvite || togglingStatus}
                className="w-full h-10 bg-red-600 text-white rounded-lg text-sm font-bold flex items-center justify-center gap-2 hover:bg-red-700 transition-all"
              >
                {removing || deletingInvite || togglingStatus ? (
                  <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : tCommon('confirm')}
              </button>
              <button 
                onClick={() => setShowConfirm(null)}
                className="w-full h-10 bg-muted text-foreground rounded-lg text-sm font-bold hover:bg-border transition-all"
              >
                {tCommon('cancel')}
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
