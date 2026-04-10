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
  Smartphone,
  Lock,
  ChevronRight,
  Eye,
  EyeOff,
  LogOut
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { LoadingState } from '@/components/ui/LoadingState';
import { CustomSelect } from '@/components/ui/CustomSelect';
import { useRouter } from 'next/navigation';

const GET_ME = gql`
  query GetMe {
    me {
      id
      email
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
      preferences
    }
  }
`;

const CHANGE_PASSWORD = gql`
  mutation ChangePassword($input: ChangePasswordInput!) {
    change_password(input: $input)
  }
`;

type TabType = 'general' | 'notifications' | 'security';

export default function ProfilePage() {
  const router = useRouter();
  const { data, loading, error, refetch } = useQuery(GET_ME);
  const [updateProfile, { loading: updating }] = useMutation(UPDATE_PROFILE);
  const [changePassword, { loading: changingPassword }] = useMutation(CHANGE_PASSWORD);
  
  const [activeTab, setActiveTab] = useState<TabType>('general');
  const [email, setEmail] = useState('');
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [minSeverity, setMinSeverity] = useState(1);
  const [currency, setCurrency] = useState('€');
  const [isMutualized, setIsMutualized] = useState(false);
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
      const prefs = JSON.parse(data.me.preferences || '{}');
      setEmailAlerts(prefs.email_alerts_enabled ?? true);
      setMinSeverity(prefs.min_severity ?? 1);
      setCurrency(prefs.currency ?? '€');
      setIsMutualized(prefs.is_mutualized ?? false);
    }
  }, [data]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateProfile({
        variables: {
          input: {
            email,
            emailAlertsEnabled: emailAlerts,
            minSeverity: parseInt(minSeverity.toString()),
            currency,
            isMutualized
          }
        }
      });
      setShowSuccess('profil mis à jour avec succès');
      setTimeout(() => setShowSuccess(null), 3000);
      refetch();
    } catch (err: any) {
      setShowError(err.message || 'erreur lors de la mise à jour');
      setTimeout(() => setShowError(null), 3000);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setShowError('les mots de passe ne correspondent pas');
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
        setShowSuccess('mot de passe modifié avec succès');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setTimeout(() => setShowSuccess(null), 3000);
      } else {
        setShowError('mot de passe actuel incorrect');
      }
    } catch (err: any) {
      setShowError(err.message || 'erreur lors du changement');
    }
  };

  if (loading) return (
    <LoadingState fullScreen message="chargement du profil..." />
  );

  const tabs = [
    { id: 'general', label: 'paramètres', icon: Shield },
    { id: 'notifications', label: 'notifications', icon: Bell },
  ];

  return (
    <div className="max-w-4xl mx-auto pb-20 px-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-primary/5 rounded-xl text-primary">
            <User className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-foreground tracking-tight">Mon Profil</h1>
            <p className="text-[10px] text-muted-foreground font-medium">Gérez vos informations et configurez vos alertes Michi.</p>
          </div>
        </div>
        <button
          onClick={() => {
            localStorage.removeItem('michi_token');
            router.push('/login');
          }}
          className="flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-xs font-bold text-red-600 bg-red-50/50 hover:bg-red-50 border border-red-100/50 hover:border-red-200 transition-all shadow-none group"
        >
          <LogOut className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" />
          Déconnexion
        </button>
      </div>

      {/* Horizontal Tabs */}
      <div className="flex border-b border-slate-100 mb-6 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={cn(
              "flex items-center gap-2 px-6 py-3 text-xs font-bold transition-all whitespace-nowrap border-b-2",
              activeTab === tab.id 
                ? "border-primary text-primary" 
                : "border-transparent text-slate-400 hover:text-slate-600"
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="space-y-8">
        {/* Messages */}
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 flex flex-col gap-2 pointer-events-none">
          {showSuccess && (
            <div className="px-6 py-3 bg-slate-900 text-white rounded-2xl flex items-center gap-3 animate-in fade-in slide-in-from-bottom-4 duration-300 pointer-events-auto">
              <CheckCircle2 className="h-4 w-4 text-primary" />
              <span className="text-[10px] font-bold tracking-widest">{showSuccess}</span>
            </div>
          )}
          {showError && (
            <div className="px-6 py-3 bg-red-600 text-white rounded-2xl flex items-center gap-3 animate-in fade-in slide-in-from-bottom-4 duration-300 pointer-events-auto">
              <AlertCircle className="h-4 w-4" />
              <span className="text-[10px] font-bold tracking-widest">{showError}</span>
            </div>
          )}
        </div>

        {activeTab === 'general' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
              {/* Section 1: Informations de base */}
              <section className="bg-white rounded-2xl border border-slate-100 overflow-hidden flex flex-col">
                <div className="p-5 border-b border-slate-50 bg-slate-50/30 flex justify-between items-center">
                  <h2 className="text-[10px] font-extrabold text-slate-900 tracking-widest flex items-center gap-2">
                    <User className="h-3 w-3 text-primary" />
                    Informations de base
                  </h2>
                  <div className="flex items-center gap-2">
                    <p className="text-[9px] font-bold text-primary tracking-tighter bg-primary/5 px-2 py-0.5 rounded-full inline-block">Compte actif</p>
                  </div>
                </div>
                <div className="p-6 space-y-6 flex-1">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-2xl bg-primary/5 flex items-center justify-center border-2 border-primary/10 text-primary">
                      <User className="h-6 w-6" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-slate-900">{email.split('@')[0]}</p>
                      <p className="text-[10px] text-slate-400 font-medium">Utilisateur Michi</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <label className="text-[9px] font-bold text-slate-400 tracking-widest ml-1">Adresse email principale</label>
                      <div className="relative">
                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                        <input 
                          type="email" 
                          value={email}
                          readOnly
                          className="w-full h-10 pl-11 pr-4 rounded-xl border-slate-200 bg-slate-100 text-slate-500 cursor-not-allowed transition-all outline-none text-xs font-medium"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </section>

              {/* Section Identifiant Boutique (Compact Banner) */}
              <section className="bg-slate-900 rounded-2xl p-6 text-white relative overflow-hidden group flex flex-col justify-center">
                <div className="absolute top-0 right-0 w-48 h-48 bg-primary/20 blur-[80px] rounded-full translate-x-1/2 -translate-y-1/2 group-hover:bg-primary/30 transition-all duration-700" />
                <div className="relative z-10 space-y-4">
                  <div className="flex items-center gap-2 text-primary">
                    <Shield className="h-3.5 w-3.5" />
                    <span className="text-[9px] font-bold tracking-widest">Identifiant boutique</span>
                  </div>
                  <div className="bg-white/5 p-4 rounded-xl border border-white/5 backdrop-blur-sm">
                    <code className="text-xs font-mono text-slate-300 block break-all">
                      {data?.me?.shopId}
                    </code>
                  </div>
                  <p className="text-[10px] text-white/40 leading-relaxed font-medium italic">
                    Identification unique requise pour synchroniser votre inventaire via les APIs Michi.
                  </p>
                </div>
              </section>
            </div>

            {/* Section 3: Paramètres Stratégiques (Sprint 13) */}
            <section className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
              <div className="p-5 border-b border-slate-50 bg-slate-50/30 flex justify-between items-center">
                <h2 className="text-[10px] font-extrabold text-slate-900 tracking-widest flex items-center gap-2">
                  <Shield className="h-3 w-3 text-indigo-600" />
                  Paramètres Stratégiques
                </h2>
              </div>
              <div className="p-6 space-y-8">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-slate-900">Devise d'affichage</p>
                    <p className="text-[10px] text-slate-500 font-medium italic">Utilisée pour tous les calculs financiers (BI et Revenue at Risk).</p>
                  </div>
                  <CustomSelect 
                    options={[
                      { value: '€', label: 'Euro (€)' },
                      { value: '$', label: 'US Dollar ($)' },
                      { value: '£', label: 'British Pound (£)' },
                      { value: 'CHF', label: 'Swiss Franc (CHF)' }
                    ]}
                    value={currency}
                    onChange={setCurrency}
                    className="w-36"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-slate-900">Mutualisation Intelligente</p>
                    <p className="text-[10px] text-slate-500 font-medium italic">Sommer les stocks de tous les produits partageant le même SKU dans l'organisation.</p>
                  </div>
                  <button 
                    type="button"
                    onClick={() => setIsMutualized(!isMutualized)}
                    className={cn(
                      "w-12 h-6 rounded-full transition-all relative flex items-center px-1",
                      isMutualized ? "bg-indigo-600" : "bg-slate-200"
                    )}
                  >
                    <div className={cn(
                      "w-4 h-4 bg-white rounded-full transition-transform duration-300",
                      isMutualized ? "translate-x-6" : "translate-x-0"
                    )} />
                  </button>
                </div>

                <div className="pt-4 flex justify-end">
                  <button 
                    onClick={handleUpdateProfile}
                    className="px-6 h-10 bg-slate-900 text-white rounded-lg text-[10px] font-bold tracking-widest hover:bg-slate-800 transition-all flex items-center gap-2"
                  >
                    <Save className="h-3 w-3" />
                    Enregistrer les paramètres
                  </button>
                </div>
              </div>
            </section>

            {/* Security Section (Password Modification) */}
            <section className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
              <div className="p-5 border-b border-slate-50 bg-slate-50/30">
                <h2 className="text-[10px] font-extrabold text-slate-900 tracking-widest flex items-center gap-2">
                  <Lock className="h-3 w-3 text-primary" />
                  Modification du mot de passe
                </h2>
              </div>
              
              <form onSubmit={handleChangePassword} className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                   <div className="space-y-1.5">
                    <label className="text-[9px] font-bold text-slate-400 tracking-widest ml-1">Mot de passe actuel</label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                      <input 
                        type={showPasswords ? "text" : "password"} 
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                        className="w-full h-10 pl-11 pr-11 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all outline-none text-xs font-medium"
                      />
                    </div>
                  </div>

                   <div className="space-y-1.5">
                    <label className="text-[9px] font-bold text-slate-400 tracking-widest ml-1">Nouveau mot de passe</label>
                    <div className="relative">
                      <Shield className="absolute left-4 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                      <input 
                        type={showPasswords ? "text" : "password"} 
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        className="w-full h-10 pl-11 pr-4 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all outline-none text-xs font-medium"
                      />
                    </div>
                  </div>

                   <div className="space-y-1.5">
                    <label className="text-[9px] font-bold text-slate-400 tracking-widest ml-1">Confirmer le nouveau</label>
                    <div className="relative">
                      <Shield className="absolute left-4 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                      <input 
                        type={showPasswords ? "text" : "password"} 
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className="w-full h-10 pl-11 pr-4 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all outline-none text-xs font-medium"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2">
                   <button 
                    type="button"
                    onClick={() => setShowPasswords(!showPasswords)}
                    className="text-[9px] font-bold text-primary tracking-widest flex items-center gap-2 hover:opacity-70 transition-all"
                  >
                    {showPasswords ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                    {showPasswords ? "Masquer" : "Afficher les mots de passe"}
                  </button>

                   <button 
                    type="submit"
                    disabled={changingPassword}
                    className="px-6 h-10 bg-slate-900 text-white rounded-lg text-[10px] font-bold tracking-widest hover:bg-slate-800 disabled:opacity-50 transition-all flex items-center gap-2"
                  >
                    {changingPassword ? (
                      <div className="h-3 w-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                       <>
                        <Lock className="h-3 w-3" />
                        Mettre à jour
                      </>
                    )}
                  </button>
                </div>
              </form>
            </section>
          </div>
        )}

        {activeTab === 'notifications' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <section className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
               <div className="p-6 border-b border-slate-50 bg-slate-50/30">
                <h2 className="text-xs font-extrabold text-slate-900 tracking-widest flex items-center gap-2">
                  <Bell className="h-3 w-3 text-primary" />
                  Préférences d'alerte
                </h2>
              </div>
              
              <form onSubmit={handleUpdateProfile} className="p-6 space-y-8">
                 <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-bold text-slate-900">Alertes emails</p>
                    <p className="text-[10px] text-slate-500 font-medium">Recevoir un condensé quotidien des alertes critiques.</p>
                  </div>
                  <button 
                    type="button"
                    onClick={() => setEmailAlerts(!emailAlerts)}
                    className={cn(
                      "w-12 h-6 rounded-full transition-all relative flex items-center px-1",
                      emailAlerts ? "bg-primary" : "bg-slate-200"
                    )}
                  >
                    <div className={cn(
                      "w-4 h-4 bg-white rounded-full transition-transform duration-300",
                      emailAlerts ? "translate-x-6" : "translate-x-0"
                    )} />
                  </button>
                </div>

                 <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-bold text-slate-900">Sévérité minimale</p>
                      <p className="text-[10px] text-slate-500 font-medium">Ne m'alerter que pour les niveaux sélectionnés et plus.</p>
                    </div>
                     <span className={cn(
                      "text-[9px] font-extrabold px-3 py-1 rounded-full border tracking-[0.2em]",
                      minSeverity == 1 ? "bg-slate-50 text-slate-500 border-slate-200" :
                      minSeverity == 2 ? "bg-amber-50 text-amber-600 border-amber-100" :
                      "bg-red-50 text-red-600 border-red-100"
                    )}>
                      {minSeverity == 1 ? "Toutes" : minSeverity == 2 ? "Importantes" : "Critiques"}
                    </span>
                  </div>
                  <div className="relative pt-4">
                    <input 
                      type="range"
                      min="1"
                      max="3"
                      value={minSeverity}
                      onChange={(e) => setMinSeverity(parseInt(e.target.value))}
                      className="w-full h-1.5 bg-slate-100 rounded-full appearance-none cursor-pointer accent-primary"
                    />
                     <div className="flex justify-between text-[10px] font-bold text-slate-400 tracking-widest mt-4">
                      <span>Niveau 1</span>
                      <span>Niveau 2</span>
                      <span>Niveau 3</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 flex justify-end">
                  <button 
                    type="submit"
                    disabled={updating}
                    className="px-6 h-10 bg-primary text-white rounded-lg text-xs font-bold hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-2"
                  >
                    {updating ? (
                      <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                       <>
                        <Save className="h-4 w-4" />
                        Appliquer
                      </>
                    )}
                  </button>
                </div>
              </form>
            </section>
          </div>
        )}

        {activeTab === 'security' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <section className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
              <div className="p-6 border-b border-slate-50 bg-slate-50/30">
                <h2 className="text-xs font-extrabold text-slate-900 tracking-widest flex items-center gap-2">
                  <Lock className="h-3 w-3 text-primary" />
                  Modification du mot de passe
                </h2>
              </div>
              
              <form onSubmit={handleChangePassword} className="p-6 space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">Mot de passe actuel</label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input 
                      type={showPasswords ? "text" : "password"} 
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                      className="w-full h-12 pl-12 pr-12 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all outline-none text-xs font-medium"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">Nouveau mot de passe</label>
                    <div className="relative">
                      <Shield className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <input 
                        type={showPasswords ? "text" : "password"} 
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        className="w-full h-10 pl-12 pr-4 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all outline-none text-xs font-medium"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-400 tracking-widest ml-1">Confirmer</label>
                    <div className="relative">
                      <Shield className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <input 
                        type={showPasswords ? "text" : "password"} 
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                        className="w-full h-12 pl-12 pr-4 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white focus:ring-4 focus:ring-primary/5 focus:border-primary/20 transition-all outline-none text-xs font-medium"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4">
                  <button 
                    type="button"
                    onClick={() => setShowPasswords(!showPasswords)}
                    className="text-[10px] font-bold text-primary tracking-widest flex items-center gap-2 hover:opacity-70 transition-all"
                  >
                    {showPasswords ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    {showPasswords ? "Masquer" : "Afficher les mots de passe"}
                  </button>

                  <button 
                    type="submit"
                    disabled={changingPassword}
                    className="px-6 h-10 bg-slate-900 text-white rounded-lg text-xs font-bold hover:bg-slate-800 disabled:opacity-50 transition-all flex items-center gap-2"
                  >
                    {changingPassword ? (
                      <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <Lock className="h-4 w-4" />
                        Mettre à jour le mot de passe
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="p-6 bg-red-50/50 border-t border-red-50 flex gap-4">
                <div className="shrink-0 p-2 bg-red-100 rounded-xl text-red-600 h-fit">
                  <AlertCircle className="h-4 w-4" />
                </div>
                 <div className="space-y-1">
                  <p className="text-xs font-bold text-red-900">Zone de sécurité</p>
                  <p className="text-[10px] text-red-600 font-medium italic leading-relaxed">
                    Une fois modifié, vous devrez vous reconnecter sur tous vos autres appareils. Assurez-vous de choisir un mot de passe robuste.
                  </p>
                </div>
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
}
