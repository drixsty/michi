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
  Eye,
  EyeOff,
  LogOut,
  ChevronRight,
  UserCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LoadingState } from '@/components/ui/LoadingState';
import { useRouter } from 'next/navigation';

const GET_ME = gql`
  query GetMe {
    me {
      id
      email
      firstName
      lastName
      shopId
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

type TabType = 'profile' | 'security' | 'notifications';

export default function ProfilePage() {
  const router = useRouter();
  const { data, loading, error, refetch } = useQuery(GET_ME);
  const [updateProfile, { loading: updating }] = useMutation(UPDATE_PROFILE);
  const [changePassword, { loading: changingPassword }] = useMutation(CHANGE_PASSWORD);
  
  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [minSeverity, setMinSeverity] = useState(1);
  const [showSuccess, setShowSuccess] = useState<string | null>(null);
  const [showError, setShowError] = useState<string | null>(null);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);

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
      setShowSuccess('Profil mis à jour avec succès');
      setTimeout(() => setShowSuccess(null), 3000);
      refetch();
    } catch (err: any) {
      setShowError(err.message || 'Erreur lors de la mise à jour');
      setTimeout(() => setShowError(null), 3000);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setShowError('Les mots de passe ne correspondent pas');
      return;
    }
    try {
      const result = await changePassword({
        variables: {
          input: {
            currentPassword,
            newPassword
          }
        }
      });
      if (result.data.change_password) {
        setShowSuccess('Mot de passe modifié avec succès');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setTimeout(() => setShowSuccess(null), 3000);
      } else {
        setShowError('Mot de passe actuel incorrect');
      }
    } catch (err: any) {
      setShowError(err.message || 'Erreur lors du changement');
    }
  };

  if (loading) return <LoadingState fullScreen message="Chargement du profil..." />;
  if (error) return <div className="p-12 text-center text-red-500">Erreur: {error.message}</div>;

  const tabs = [
    { id: 'profile', label: 'Profil', icon: UserCircle },
    { id: 'security', label: 'Sécurité', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
  ] as const;

  return (
    <div className="max-w-4xl mx-auto pb-20 px-4 mt-4 animate-in fade-in duration-500">
      
      {/* Header compact */}
      <div className="flex items-center justify-between mb-6 pb-6 border-b border-border">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center text-primary border border-primary/20 shrink-0">
            <User className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground tracking-tight">Paramètres du profil</h1>
            <p className="text-[13px] text-muted-foreground">Gérez vos informations personnelles et votre sécurité.</p>
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
          Déconnexion
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[200px_1fr] gap-8">
        
        {/* Barre latérale de navigation style Linear */}
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

        {/* Contenu principal */}
        <main className="space-y-6">
          
          {/* Notifications Success/Error */}
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
                  <h2 className="text-[13px] font-semibold text-foreground">Informations personnelles</h2>
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
                      <label className="text-[12px] font-medium text-muted-foreground ml-0.5">Prénom</label>
                      <input 
                        type="text" 
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="Votre prénom"
                        className="w-full h-9 px-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all outline-none text-sm"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[12px] font-medium text-muted-foreground ml-0.5">Nom</label>
                      <input 
                        type="text" 
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder="Votre nom"
                        className="w-full h-9 px-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all outline-none text-sm"
                      />
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[12px] font-medium text-muted-foreground ml-0.5">Adresse email</label>
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
                          Sauvegarder
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
                  <h2 className="text-[13px] font-semibold text-foreground">Sécurité du compte</h2>
                </div>
                
                <form onSubmit={handleChangePassword} className="p-5 space-y-4">
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-[12px] font-medium text-muted-foreground ml-0.5">Mot de passe actuel</label>
                      <input 
                        type={showPasswords ? "text" : "password"} 
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                        className="w-full h-9 px-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all outline-none text-sm"
                      />
                    </div>
                    
                    <div className="grid grid-cols-1 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-[12px] font-medium text-muted-foreground ml-0.5">Nouveau mot de passe</label>
                        <input 
                          type={showPasswords ? "text" : "password"} 
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          required
                          className="w-full h-9 px-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all outline-none text-sm"
                        />
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-[12px] font-medium text-muted-foreground ml-0.5">Confirmer le mot de passe</label>
                        <input 
                          type={showPasswords ? "text" : "password"} 
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          required
                          className="w-full h-9 px-3 rounded-lg border border-border bg-background focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all outline-none text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <button 
                      type="button"
                      onClick={() => setShowPasswords(!showPasswords)}
                      className="text-[12px] font-medium text-primary hover:underline flex items-center gap-1.5"
                    >
                      {showPasswords ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                      {showPasswords ? "Masquer" : "Afficher"}
                    </button>

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
                          Mettre à jour le mot de passe
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </section>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6 animate-in fade-in duration-300">
              <section className="bg-white rounded-lg border border-border overflow-hidden">
                <div className="px-5 py-4 border-b border-border bg-muted/20">
                  <h2 className="text-[13px] font-semibold text-foreground">Centre de notifications</h2>
                </div>
                
                <div className="p-5 space-y-8">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <p className="text-[14px] font-medium text-foreground">Alertes par email</p>
                      <p className="text-[13px] text-muted-foreground">Recevoir un condensé quotidien de vos alertes critiques.</p>
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
                        <p className="text-[14px] font-medium text-foreground">Sévérité minimale</p>
                        <p className="text-[13px] text-muted-foreground">Niveau d'urgence requis pour déclencher un email.</p>
                      </div>
                      <span className={cn(
                        "text-[10px] font-bold px-2 py-0.5 rounded border uppercase",
                        minSeverity === 1 ? "bg-muted text-muted-foreground border-border" :
                        minSeverity === 2 ? "bg-amber-50 text-amber-600 border-amber-100" :
                        "bg-red-50 text-red-600 border-red-100"
                      )}>
                        {minSeverity === 1 ? "Standard" : minSeverity === 2 ? "Urgent" : "Critique"}
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
                        <span>Standard</span>
                        <span>Urgent</span>
                        <span>Critique</span>
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
                          Sauvegarder
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
    </div>
  );
}
