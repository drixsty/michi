"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { 
  ShoppingBag, 
  Package, 
  FileText,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Target,
  TrendingUp,
  Zap,
  CheckCircle2,
  Rocket,
  Plus
} from 'lucide-react';
import { useMutation, useQuery, useApolloClient, gql } from '@apollo/client';
import { useStore } from '../../../context/StoreContext';
import { useTranslations } from 'next-intl';
import { AddSourcePanel } from '@/components/dashboard/AddSourcePanel';
import { Input } from '@/components/ui/Input';
import { cn } from '@/lib/utils';

const GET_ONBOARDING_DATA = gql`
  query GetOnboardingData {
    currentOrganization {
      id
      name
      onboardingStep
      onboardingCompleted
    }
    sources {
      id
      platform
      connected
    }
  }
`;

const CREATE_ORG = gql`
  mutation CreateOrg($name: String!) {
    createOrganization(name: $name) {
      token
      user {
        id
      }
    }
  }
`;

const UPDATE_ORG = gql`
  mutation UpdateOrg($input: UpdateOrganizationInput!) {
    updateOrganization(input: $input) {
      id
      onboardingStep
      onboardingCompleted
    }
  }
`;

type Step = 'welcome' | 'identity' | 'goal' | 'connect' | 'sync';

const STEPS: { id: Step; labelKey: string }[] = [
  { id: 'welcome', labelKey: 'progress.welcome' },
  { id: 'identity', labelKey: 'progress.identity' },
  { id: 'goal', labelKey: 'progress.goal' },
  { id: 'connect', labelKey: 'progress.connect' },
  { id: 'sync', labelKey: 'progress.sync' },
];

export default function OnboardingPage() {
  const t = useTranslations('onboarding');
  const router = useRouter();
  const { refreshUser } = useStore();
  
  const { data, loading, refetch } = useQuery(GET_ONBOARDING_DATA, {
    fetchPolicy: 'network-only'
  });
  
  const [updateOrg] = useMutation(UPDATE_ORG);
  const [createOrg] = useMutation(CREATE_ORG);
  const client = useApolloClient();
  
  const [currentStep, setCurrentStep] = useState<Step>('welcome');
  const [isAddSourceOpen, setIsAddSourceOpen] = useState(false);
  const [orgName, setOrgName] = useState('');
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [isSyncComplete, setIsSyncComplete] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);

  const connectedSources = data?.sources || [];
  const hasConnectedSources = connectedSources.length > 0;

  // Sync state with backend data
  useEffect(() => {
    if (data?.currentOrganization) {
      const { onboardingStep, name } = data.currentOrganization;
      if (onboardingStep) setCurrentStep(onboardingStep as Step);
      if (name) setOrgName(name);
    }
  }, [data]);

  // Fake sync timer for UX
  useEffect(() => {
    if (currentStep === 'sync') {
      const timer = setTimeout(() => {
        setIsSyncComplete(true);
      }, 4000); 
      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  const handleNext = async (nextStep: Step) => {
    try {
      if (!data?.currentOrganization) {
        // First step: Create the organization
        const { data: createData } = await createOrg({
          variables: { name: orgName || "Ma Boutique" }
        });
        
        if (createData?.createOrganization?.token) {
          localStorage.setItem('michi_token', createData.createOrganization.token);
          localStorage.setItem('michi_onboarding_finished', 'true'); // NEW: Early flag to prevent redirect
          // Force a full refetch to have context for subsequent steps
          await client.resetStore();
          await refreshUser(); // NEW: Update StoreContext memberships
        }
      }

      await updateOrg({
        variables: {
          input: { 
            onboardingStep: nextStep, 
            name: orgName || data?.currentOrganization?.name 
          }
        }
      });
      setCurrentStep(nextStep);
      await refetch();
    } catch (err) {
      console.error("[Onboarding] Navigation Error:", err);
    }
  };

  const handleBack = async () => {
    const currentIndex = STEPS.findIndex(s => s.id === currentStep);
    if (currentIndex > 0) {
      const prevStep = STEPS[currentIndex - 1].id;
      await handleNext(prevStep);
    }
  };

  const handleFinish = async () => {
    if (isFinishing) return;
    
    try {
      setIsFinishing(true);
      const result = await updateOrg({
        variables: {
          input: { 
            name: orgName || data?.currentOrganization?.name, 
            onboardingCompleted: true, 
            onboardingStep: 'sync' 
          }
        }
      });
      
      if (result.data) {
        // Marquer l'onboarding comme fini localement pour éviter les boucles de redirection
        localStorage.setItem('michi_onboarding_finished', 'true');
        // Nettoyage complet pour éviter les données de cache périmées
        await client.clearStore();
        // Utiliser href pour forcer un rechargement complet du navigateur
        window.location.href = '/dashboard';
      } else {
        setIsFinishing(false);
      }
    } catch (err) {
      console.error("[Onboarding] Finish Error:", err);
      setIsFinishing(false);
    }
  };

  if (loading && !data) return null;

  const currentStepIndex = STEPS.findIndex(s => s.id === currentStep);

  return (
    <div className="min-h-[100dvh] bg-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[300px] bg-gradient-to-b from-slate-50 to-transparent -z-10" />

      {/* Stepper Labels - Compact */}
      <div className="w-full max-w-md mb-8 lg:mb-12">
        <div className="flex justify-between px-1 gap-1.5">
          {STEPS.map((step, idx) => (
            <div 
              key={step.id} 
              className={cn(
                "h-1 rounded-full transition-all duration-500 flex-1",
                idx <= currentStepIndex ? "bg-slate-900" : "bg-slate-100"
              )}
            />
          ))}
        </div>
        <div className="mt-3 text-center">
          <span className="text-[10px] font-bold text-slate-400">
            {t(STEPS[currentStepIndex].labelKey)} — {currentStepIndex + 1}/{STEPS.length}
          </span>
        </div>
      </div>

      <div className="max-w-md w-full z-10">
        <AnimatePresence mode="wait">
          {currentStep === 'welcome' && (
            <motion.div
              key="welcome"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="bg-white p-8 rounded-lg border border-slate-100 text-center shadow-sm"
            >
              <div className="w-12 h-12 bg-slate-900 rounded-lg flex items-center justify-center mx-auto mb-6">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 mb-3">{t('welcome.title')}</h1>
              <p className="text-slate-500 text-sm mb-8 leading-relaxed">
                {t('welcome.description')}
              </p>
              <button 
                onClick={() => handleNext('identity')}
                className="w-full h-11 bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold rounded-lg transition-all flex items-center justify-center gap-2"
              >
                {t('welcome.button')}
                <ChevronRight className="w-4 h-4" />
              </button>
            </motion.div>
          )}

          {(currentStep === 'identity' || currentStep === 'goal' || currentStep === 'connect') && (
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white p-8 rounded-lg border border-slate-100 shadow-sm"
            >
              <h1 className="text-xl font-bold text-slate-900 mb-1">{t(`${currentStep}.title`)}</h1>
              
              <div className="mt-6">
                {currentStep === 'identity' && (
                  <Input 
                    label={t('identity.label')}
                    autoFocus
                    value={orgName}
                    onChange={(e) => setOrgName(e.target.value)}
                    placeholder={t('identity.placeholder')}
                    className="rounded-lg"
                  />
                )}

                {currentStep === 'goal' && (
                  <div className="space-y-2">
                    <p className="text-xs text-slate-500 mb-4">{t('goal.description')}</p>
                    {[
                      { id: 'stockouts', icon: Target },
                      { id: 'capital', icon: Zap },
                      { id: 'growth', icon: TrendingUp },
                    ].map((goal) => (
                      <button 
                        key={goal.id}
                        onClick={() => setSelectedGoal(goal.id)}
                        className={cn(
                          "flex items-center gap-3 w-full p-4 min-h-[60px] rounded-lg border transition-all text-left",
                          selectedGoal === goal.id 
                            ? "border-slate-900 bg-slate-900 text-white shadow-lg shadow-slate-900/10" 
                            : "border-slate-100 bg-slate-50 hover:bg-white hover:border-slate-200"
                        )}
                      >
                        <goal.icon className={cn("w-4 h-4", selectedGoal === goal.id ? "text-white" : "text-slate-400")} />
                        <div>
                          <h3 className="font-bold text-xs">{t(`goal.options.${goal.id}.title`)}</h3>
                          <p className={cn("text-[10px] opacity-70", selectedGoal === goal.id ? "text-white" : "text-slate-500")}>
                            {t(`goal.options.${goal.id}.desc`)}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {currentStep === 'connect' && (
                  <div className="space-y-4">
                    <p className="text-xs text-slate-500 mb-4">{t('connect.description')}</p>
                    <div className="grid grid-cols-1 gap-2">
                      {[
                        { id: 'shopify', icon: ShoppingBag, label: t('connect.platforms.shopify'), active: true },
                        { id: 'csv', icon: FileText, label: t('connect.platforms.csv'), active: true },
                        { id: 'woocommerce', icon: Package, label: t('connect.platforms.woocommerce'), active: false },
                      ].map((platform) => {
                        const isConnected = connectedSources.some((s: any) => s.platform.toLowerCase() === platform.id);
                        
                        return (
                          <button 
                            key={platform.id}
                            disabled={!platform.active}
                            onClick={() => platform.id === 'csv' ? router.push('/dashboard/import') : setIsAddSourceOpen(true)}
                            className={cn(
                              "flex items-center justify-between p-3 rounded-lg border transition-all text-left group",
                              platform.active 
                                ? isConnected 
                                  ? "border-emerald-100 bg-emerald-50/30"
                                  : "border-slate-100 bg-slate-50 hover:border-slate-900 hover:bg-white" 
                                : "opacity-40 cursor-not-allowed border-slate-50 shadow-none"
                            )}
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 bg-white rounded-lg border border-slate-100 flex items-center justify-center transition-colors group-hover:border-slate-900/10">
                                <platform.icon className={cn("w-4 h-4", isConnected ? "text-emerald-500" : "text-slate-900")} />
                              </div>
                              <span className={cn("font-bold text-xs", isConnected ? "text-emerald-700" : "text-slate-900")}>
                                {platform.label}
                              </span>
                            </div>
                            
                            {isConnected ? (
                              <div className="flex items-center gap-1 bg-emerald-500 text-white px-2 py-0.5 rounded-full text-[9px] font-bold">
                                <CheckCircle2 className="w-2.5 h-2.5" />
                                <span>Connecté</span>
                              </div>
                            ) : (
                              platform.active && (
                                <div className="p-1 rounded-lg bg-white border border-slate-100 transition-colors group-hover:border-slate-900/20">
                                  <Plus className="w-3 h-3 text-slate-400" />
                                </div>
                              )
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-8 lg:mt-10 flex flex-col gap-3">
                <button 
                  onClick={() => {
                    if (currentStep === 'identity') handleNext('goal');
                    if (currentStep === 'goal') handleNext('connect');
                    if (currentStep === 'connect') handleNext('sync');
                  }}
                  disabled={
                    (currentStep === 'identity' && !orgName.trim()) || 
                    (currentStep === 'goal' && !selectedGoal) ||
                    (currentStep === 'connect' && !hasConnectedSources)
                  }
                  className="w-full h-11 bg-slate-900 hover:bg-slate-800 disabled:opacity-30 disabled:bg-slate-200 disabled:text-slate-400 text-white text-sm font-bold rounded-lg transition-all shadow-md shadow-slate-900/5 active:scale-[0.98]"
                >
                  {t(`${currentStep}.button`)}
                </button>
                <button 
                  onClick={handleBack}
                  className="w-full h-11 text-slate-400 hover:text-slate-900 text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  {t('goal.back')}
                </button>
              </div>
            </motion.div>
          )}

          {currentStep === 'sync' && (
            <motion.div
              key="sync"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.02 }}
              className="bg-white p-8 rounded-lg border border-slate-100 shadow-sm text-center"
            >
              <h1 className="text-xl font-bold text-slate-900 mb-8">{t('sync.title')}</h1>
              
              <div className="space-y-4 mb-10 text-left max-w-[200px] mx-auto">
                {[
                  { key: 'analyze', done: true },
                  { key: 'forecast', done: isSyncComplete },
                  { key: 'init', done: isSyncComplete },
                ].map((item) => (
                  <div key={item.key} className="flex items-center gap-3">
                    <div className={cn(
                      "w-5 h-5 rounded-full flex items-center justify-center transition-all",
                      item.done ? "bg-emerald-500 text-white" : "bg-slate-100 text-slate-300"
                    )}>
                      {item.done ? <CheckCircle2 className="w-3 h-3" /> : <div className="w-1.5 h-1.5 rounded-full bg-current" />}
                    </div>
                    <span className={cn(
                      "text-xs font-bold transition-all",
                      item.done ? "text-slate-900" : "text-slate-300"
                    )}>
                      {t(`sync.steps.${item.key}`)}
                    </span>
                  </div>
                ))}
              </div>

              <button 
                onClick={handleFinish}
                disabled={!isSyncComplete || isFinishing}
                className="w-full h-11 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-50 disabled:text-slate-300 text-white text-sm font-bold rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-slate-900/10 active:scale-[0.98]"
              >
                {isFinishing ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Rocket className="w-4 h-4" />
                )}
                {isFinishing ? t('sync.finishing') : t('sync.button')}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <AddSourcePanel 
        isOpen={isAddSourceOpen} 
        onClose={() => setIsAddSourceOpen(false)} 
        onSuccess={() => {
          setIsAddSourceOpen(false);
          refetch();
        }}
        connectedPlatforms={connectedSources.map((s: any) => s.platform)}
      />
    </div>
  );
}
