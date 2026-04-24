'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, gql } from '@apollo/client';
import {
  User,
  Mail,
  Bell,
  Shield,
  Save,
  CheckCircle2,
  AlertCircle,
  Lock,
  LogOut,
  ChevronRight,
  UserCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LoadingState } from '@/components/ui/LoadingState';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { PasswordInput } from '@/components/ui/PasswordInput';
import Link from 'next/link';
import { TwoFactorSetup } from '@/components/profile/TwoFactorSetup';

const GET_ME = gql`
  query GetMe {
    me {
      id
      email
      firstName
      lastName
      twoFactorEnabled
      preferences
    }
  }
`;

const UPDATE_PROFILE = gql`
  mutation UpdateProfile($input: UpdateProfileInput!) {
    update_profile(input: $input) {
      id
      email
      firstName
      lastName
      preferences
    }
  }
`;

const CHANGE_PASSWORD = gql`
  mutation ChangePassword($input: ChangePasswordInput!) {
    change_password(input: $input)
  }
`;

const EXPORT_DATA = gql`
  mutation ExportUserData {
    exportUserData {
      dataJson
    }
  }
`;

const DELETE_ACCOUNT = gql`
  mutation DeleteAccount {
    deleteAccount
  }
`;

type TabType = 'profile' | 'security' | 'notifications';

export default function ProfilePage() {
  const t = useTranslations('profile');
  const router = useRouter();
  const { data, loading, error, refetch } = useQuery(GET_ME);
  const [updateProfile, { loading: updating }] = useMutation(UPDATE_PROFILE);
  const [changePassword, { loading: changingPassword }] = useMutation(CHANGE_PASSWORD);
  const [exportData, { loading: exporting }] = useMutation(EXPORT_DATA);
  const [deleteAccount, { loading: deleting }] = useMutation(DELETE_ACCOUNT);

  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [minSeverity, setMinSeverity] = useState(1);
  const [showSuccess, setShowSuccess] = useState<string | null>(null);
  const [showError, setShowError] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  useEffect(() => {
    if (data?.me) {
      setEmail(data.me.email);
      setFirstName(data.me.firstName || '');
      setLastName(data.me.lastName || '');
      try {
        const prefs = JSON.parse(data.me.preferences || '{}');
        setEmailAlerts(prefs.email_alerts_enabled ?? true);
        setMinSeverity(prefs.min_severity ?? 1);
      } catch (e) {
        console.error("Failed to parse preferences", e);
      }
    }
  }, [data]);

  const handleUpdateProfile = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      await updateProfile({
        variables: {
          input: {
            email,
            firstName,
            lastName,
            emailAlertsEnabled: emailAlerts,
            minSeverity: parseInt(minSeverity.toString()),
          }
        }
      });
      setShowSuccess(t('updateSuccess'));
      setTimeout(() => setShowSuccess(null), 3000);
      refetch();
    } catch (err: any) {
      setShowError(err.message || t('updateError'));
      setTimeout(() => setShowError(null), 3000);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setShowError(t('security.passwordMismatch'));
      return;
    }
    try {
      const result = await changePassword({
        variables: {
          input: { currentPassword, newPassword }
        }
      });
      if (result.data.change_password) {
        setShowSuccess(t('security.passwordSuccess'));
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setTimeout(() => setShowSuccess(null), 3000);
      } else {
        setShowError(t('security.incorrectPassword'));
      }
    } catch (err: any) {
      setShowError(err.message || t('security.passwordError'));
    }
  };

  const handleExportData = async () => {
    try {
      const { data } = await exportData();
      const blob = new Blob([data.exportUserData.dataJson], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `michi-data-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== 'SUPPRIMER') {
      toast.error(t('gdpr.deleteErrorText'));
      return;
    }

    try {
      const { data: deleteData } = await deleteAccount();
      if (deleteData?.deleteAccount) {
        toast.success(t('gdpr.deleteSuccess'));
        router.push('/login');
      }
    } catch (err: any) {
      toast.error(err.message || t('gdpr.deleteError'));
    }
  };

  if (loading) return <LoadingState fullScreen message={t('loading')} />;
  if (error) return <div className="p-12 text-center text-red-500">{error.message}</div>;

  const tabs = [
    { id: 'profile' as TabType, label: t('tabs.profile'), icon: UserCircle },
    { id: 'security' as TabType, label: t('tabs.security'), icon: Shield },
    { id: 'notifications' as TabType, label: t('tabs.notifications'), icon: Bell },
  ];

  const severityLabels: Record<number, string> = {
    1: t('notifications.standard'),
    2: t('notifications.urgent'),
    3: t('notifications.critical'),
  };

  return (
    <div className="max-w-4xl mx-auto pb-20 px-4 mt-4 animate-in fade-in duration-500">

      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-6 border-b border-border">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shrink-0">
            <User className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground tracking-tight">{t('settings')}</h1>
            <p className="text-[13px] text-muted-foreground">{t('settingsSubtitle')}</p>
          </div>
        </div>

        <button
          onClick={() => {
            localStorage.removeItem('michi_token');
            router.push('/login');
          }}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium text-muted-foreground hover:text-red-500 hover:bg-red-50 transition-all border border-transparent hover:border-red-100"
        >
          <LogOut className="h-3.5 w-3.5" />
          {t('logout')}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-8">

        {/* Sidebar */}
        <aside className="space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all",
                activeTab === tab.id
                  ? "bg-primary/5 text-primary font-semibold"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <tab.icon className={cn("h-4 w-4", activeTab === tab.id ? "text-primary" : "text-muted-foreground/60")} />
              {tab.label}
              {activeTab === tab.id && <ChevronRight className="h-3 w-3 ml-auto opacity-50" />}
            </button>
          ))}
        </aside>

        {/* Main content */}
        <main className="space-y-6">

          {(showSuccess || showError) && (
            <div className={cn(
              "p-3 rounded-lg border text-[13px] flex items-center gap-3 animate-in slide-in-from-top-1 duration-300",
              showSuccess ? "bg-emerald-50 border-emerald-100 text-emerald-600" : "bg-red-50 border-red-100 text-red-600"
            )}>
              {showSuccess ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
              {showSuccess || showError}
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <section className="bg-white rounded-lg border border-border overflow-hidden">
                <div className="px-5 py-4 border-b border-border bg-muted/20">
                  <h2 className="text-[13px] font-semibold text-foreground">{t('personalInfo')}</h2>
                </div>
                <div className="p-5 space-y-5">
                  <div className="flex items-center gap-5 pb-2">
                    <div className="w-14 h-14 rounded-lg bg-muted flex items-center justify-center text-muted-foreground border border-border text-xl font-bold">
                      {firstName?.[0] || email?.[0]?.toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-foreground">
                        {firstName || lastName ? `${firstName} ${lastName}` : email.split('@')[0]}
                      </p>
                      <p className="text-[13px] text-muted-foreground">{email}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-1">
                    <div className="space-y-1.5">
                      <label className="text-[12px] font-medium text-muted-foreground ml-0.5">{t('firstNameLabel')}</label>
                      <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder={t('firstNamePlaceholder')}
                        className="w-full h-9 px-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all outline-none text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[12px] font-medium text-muted-foreground ml-0.5">{t('lastNameLabel')}</label>
                      <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder={t('lastNamePlaceholder')}
                        className="w-full h-9 px-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all outline-none text-sm"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[12px] font-medium text-muted-foreground ml-0.5">{t('emailLabel')}</label>
                    <div className="relative group">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50 group-focus-within:text-primary transition-colors" />
                      <input
                        type="email"
                        value={email}
                        disabled
                        className="w-full h-9 pl-9 pr-4 rounded-lg border border-border bg-muted/50 text-muted-foreground cursor-not-allowed text-sm"
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      onClick={() => handleUpdateProfile()}
                      disabled={updating}
                      className="h-9 px-6 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-90 transition-all flex items-center gap-2"
                    >
                      {updating ? (
                        <div className="h-3.5 w-3.5 border-2 border-background/30 border-t-background rounded-full animate-spin" />
                      ) : (
                        <>
                          <Save className="h-3.5 w-3.5" />
                          {t('save')}
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <section className="bg-white rounded-lg border border-border overflow-hidden">
                <div className="px-5 py-4 border-b border-border bg-muted/20">
                  <h2 className="text-[13px] font-semibold text-foreground">{t('security.title')}</h2>
                </div>

                <form onSubmit={handleChangePassword} className="p-5 space-y-4">
                  <div className="space-y-4">
                    <PasswordInput
                      label={t('security.currentPassword')}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <PasswordInput
                        label={t('security.newPassword')}
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        minLength={8}
                      />
                      <PasswordInput
                        label={t('security.confirmPassword')}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        minLength={8}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <Link 
                      href="/forgot-password"
                      className="text-[12px] font-medium text-primary hover:underline"
                    >
                      {t('security.forgotPasswordLink')}
                    </Link>

                    <button
                      type="submit"
                      disabled={changingPassword}
                      className="h-9 px-6 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-90 transition-all flex items-center gap-2"
                    >
                      {changingPassword ? (
                        <div className="h-3.5 w-3.5 border-2 border-background/30 border-t-background rounded-full animate-spin" />
                      ) : (
                        <>
                          <Lock className="h-3.5 w-3.5" />
                          {t('security.updateButton')}
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </section>

              {/* 2FA Section */}
              <TwoFactorSetup 
                isEnabled={data?.me?.twoFactorEnabled} 
                onStatusChange={() => refetch()} 
              />

              {/* Data Portability */}
              <section className="bg-white rounded-lg border border-border overflow-hidden">
                <div className="px-5 py-4 border-b border-border bg-muted/20">
                  <h2 className="text-[13px] font-semibold text-foreground">{t('gdpr.exportTitle')}</h2>
                </div>
                <div className="p-5 flex items-center justify-between gap-4">
                  <div className="space-y-0.5">
                    <p className="text-[13px] text-muted-foreground leading-relaxed">
                      {t('gdpr.exportDesc')}
                    </p>
                  </div>
                  <button
                    onClick={handleExportData}
                    disabled={exporting}
                    className="h-9 px-4 border border-border rounded-lg text-[12px] font-semibold hover:bg-muted transition-all shrink-0 flex items-center gap-2"
                  >
                    {exporting ? (
                      <div className="h-3.5 w-3.5 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                    ) : (
                      <>
                        <LogOut className="h-3.5 w-3.5 rotate-90" />
                        {t('gdpr.exportButton')}
                      </>
                    )}
                  </button>
                </div>
              </section>

              {/* Danger Zone */}
              <div className="pt-2">
                <div className="bg-red-50/50 rounded-lg border border-red-100 p-5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <h3 className="text-[13px] font-bold text-red-600 flex items-center gap-2">
                      <AlertCircle className="h-3.5 w-3.5" />
                      {t('gdpr.deleteTitle')}
                    </h3>
                    <p className="text-[12px] text-red-600/70 max-w-md italic">
                      {t('gdpr.deleteDesc')}
                    </p>
                  </div>
                  <button
                    onClick={() => setIsDeleteModalOpen(true)}
                    disabled={deleting}
                    className="h-9 px-4 bg-red-600 text-white rounded-lg text-[12px] font-bold hover:bg-red-700 transition-all shrink-0 flex items-center gap-2 shadow-sm"
                  >
                    {t('deleteAccount')}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <section className="bg-white rounded-lg border border-border overflow-hidden">
                <div className="px-5 py-4 border-b border-border bg-muted/20">
                  <h2 className="text-[13px] font-semibold text-foreground">{t('notifications.title')}</h2>
                </div>

                <div className="p-5 space-y-8">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <p className="text-[14px] font-medium text-foreground">{t('notifications.emailAlerts')}</p>
                      <p className="text-[13px] text-muted-foreground">{t('notifications.emailAlertsDesc')}</p>
                    </div>
                    <button
                      onClick={() => setEmailAlerts(!emailAlerts)}
                      className={cn(
                        "w-9 h-5 rounded-full transition-all relative flex items-center px-0.5 border border-border",
                        emailAlerts ? "bg-primary border-primary" : "bg-muted"
                      )}
                    >
                      <div className={cn(
                        "w-3.5 h-3.5 bg-white rounded-full transition-transform duration-200 shadow-sm",
                        emailAlerts ? "translate-x-4" : "translate-x-0"
                      )} />
                    </button>
                  </div>

                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <p className="text-[14px] font-medium text-foreground">{t('notifications.minSeverity')}</p>
                        <p className="text-[13px] text-muted-foreground">{t('notifications.minSeverityDesc')}</p>
                      </div>
                      <span className={cn(
                        "text-[10px] font-bold px-2 py-0.5 rounded border uppercase",
                        minSeverity === 1 ? "bg-muted text-muted-foreground border-border" :
                        minSeverity === 2 ? "bg-amber-50 text-amber-600 border-amber-100" :
                        "bg-red-50 text-red-600 border-red-100"
                      )}>
                        {severityLabels[minSeverity]}
                      </span>
                    </div>

                    <div className="pt-2 px-1">
                      <input
                        type="range"
                        min="1"
                        max="3"
                        step="1"
                        value={minSeverity}
                        onChange={(e) => setMinSeverity(parseInt(e.target.value))}
                        className="w-full h-1.5 bg-muted rounded-full appearance-none cursor-pointer accent-primary"
                      />
                      <div className="flex justify-between text-[11px] font-medium text-muted-foreground mt-3">
                        <span>{t('notifications.standard')}</span>
                        <span>{t('notifications.urgent')}</span>
                        <span>{t('notifications.critical')}</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-border flex justify-end">
                    <button
                      onClick={() => handleUpdateProfile()}
                      disabled={updating}
                      className="h-9 px-6 bg-foreground text-background rounded-lg text-[13px] font-semibold hover:opacity-90 transition-all flex items-center gap-2"
                    >
                      {updating ? (
                        <div className="h-3.5 w-3.5 border-2 border-background/30 border-t-background rounded-full animate-spin" />
                      ) : (
                        <>
                          <Save className="h-3.5 w-3.5" />
                          {t('save')}
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </section>
            </div>
          )}

        </main>
      </div>

      {/* Account Deletion Confirmation Modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div 
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" 
            onClick={() => !deleting && setIsDeleteModalOpen(false)} 
          />
          <div className="relative bg-white w-full max-w-md rounded-lg shadow-2xl border border-border p-6 space-y-6 animate-in zoom-in-95 duration-200">
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-50 text-red-500 flex items-center justify-center">
                <AlertCircle className="h-6 w-6" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-bold text-foreground">{t('gdpr.deleteConfirmTitle')}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {t('gdpr.deleteConfirmDesc')}
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="p-3 bg-muted/50 rounded-lg border border-border text-[12px] text-muted-foreground text-center italic">
                {t('gdpr.deleteTypeToConfirm')} <span className="font-bold text-red-600 not-italic">SUPPRIMER</span>
              </div>
              <input
                type="text"
                value={deleteConfirmation}
                onChange={(e) => setDeleteConfirmation(e.target.value)}
                placeholder="SUPPRIMER"
                className="w-full h-11 px-4 rounded-lg border border-border bg-background text-sm text-center font-bold tracking-widest transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                disabled={deleting}
                onClick={() => setIsDeleteModalOpen(false)}
                className="flex-1 h-11 rounded-lg text-sm font-bold text-muted-foreground hover:bg-muted transition-all"
              >
                {t('cancel')}
              </button>
              <button
                disabled={deleting || deleteConfirmation !== 'SUPPRIMER'}
                onClick={handleDeleteAccount}
                className="flex-[2] h-11 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-red-600/10 disabled:opacity-50 disabled:shadow-none"
              >
                {deleting && <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                {t('deleteAccount')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
