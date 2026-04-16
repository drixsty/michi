'use client';

import React, { useState } from 'react';
import { useMutation, gql } from '@apollo/client';
import { 
  ShoppingCart, 
  Globe, 
  Anchor, 
  ArrowRight,
  Database,
  Search,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Lock,
  ExternalLink,
  Plus
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { cn } from '@/lib/utils';
import { SidePanel } from '../ui/SidePanel';

// Reuse existing mutation from ConnectorsGrid (assuming it's compatible)
const TOGGLE_SOURCE = gql`
  mutation ToggleSource($platform: String!, $connected: Boolean!) {
    toggleSource(platform: $platform, connected: $connected) {
      id
      connected
    }
  }
`;

const CONNECTOR_TYPES = [
  {
    id: 'shopify',
    name: 'Shopify',
    description: 'Import automatique de vos produits, variantes et historique de ventes.',
    icon: ShoppingCart,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    status: 'Direct'
  },
  {
    id: 'amazon',
    name: 'Amazon Seller',
    description: 'Connexion via Seller Central MWS pour synchroniser votre inventaire.',
    icon: Anchor,
    color: 'text-orange-600',
    bg: 'bg-orange-50',
    status: 'Direct'
  },
  {
    id: 'woocommerce',
    name: 'WooCommerce',
    description: 'Utilisez vos clés API Consumer/Secret pour lier votre boutique.',
    icon: Globe,
    color: 'text-indigo-600',
    bg: 'bg-indigo-50',
    status: 'Direct'
  }
];

interface AddSourcePanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  connectedPlatforms: string[];
}

export function AddSourcePanel({ isOpen, onClose, onSuccess, connectedPlatforms }: AddSourcePanelProps) {
  const [step, setStep] = useState<'selection' | 'config'>('selection');
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  
  // Form states
  const [shopUrl, setShopUrl] = useState('');
  const [sellerId, setSellerId] = useState('');
  const [mwsToken, setMwsToken] = useState('');
  const [wooUrl, setWooUrl] = useState('');
  const [wooKey, setWooKey] = useState('');
  const [wooSecret, setWooSecret] = useState('');

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const t = useTranslations('dashboard.connectors.add');
  const tCommon = useTranslations('common');

  const connectorData: Record<string, any> = {
    shopify: {
      name: 'Shopify',
      description: t('shopify.desc'),
      icon: ShoppingCart,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50'
    },
    amazon: {
      name: 'Amazon Seller',
      description: t('amazon.desc'),
      icon: Anchor,
      color: 'text-orange-600',
      bg: 'bg-orange-50'
    },
    woocommerce: {
      name: 'WooCommerce',
      description: t('woocommerce.desc'),
      icon: Globe,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50'
    }
  };

  const availablePlatforms = Object.keys(connectorData)
    .filter(id => !connectedPlatforms.some(cp => cp.toLowerCase() === id.toLowerCase()))
    .map(id => ({ id, ...connectorData[id] }));

  const [toggleSource, { loading: toggling }] = useMutation(TOGGLE_SOURCE, {
    onCompleted: () => {
      setSuccess(true);
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 1500);
    },
    onError: (err) => {
      setError(err.message);
    }
  });

  const handleClose = () => {
    setStep('selection');
    setSelectedPlatform(null);
    setShopUrl('');
    setSellerId('');
    setMwsToken('');
    setWooUrl('');
    setWooKey('');
    setWooSecret('');
    setError(null);
    setSuccess(false);
    onClose();
  };

  const handleSelectPlatform = (id: string) => {
    setSelectedPlatform(id);
    setStep('config');
  };

  const fillTestData = () => {
    if (selectedPlatform === 'shopify') setShopUrl('michi-test-shop');
    if (selectedPlatform === 'amazon') {
      setSellerId('TEST_SELLER_ID');
      setMwsToken('amzn.mws.test-token-12345');
    }
    if (selectedPlatform === 'woocommerce') {
      setWooUrl('https://example-shop.com');
      setWooKey('ck_test_key_123');
      setWooSecret('cs_test_secret_456');
    }
  };

  const handleConnect = async () => {
    if (!selectedPlatform) return;
    setError(null);
    
    // Simple validation
    if (selectedPlatform === 'shopify' && !shopUrl) {
      setError(t("shopify.error"));
      return;
    }
    
    // --- Sprint 15 : Real Connection for Shopify ---
    // Bypass real connection if user clicked "Use test data" (michi-test-shop)
    if (selectedPlatform === 'shopify' && shopUrl !== 'michi-test-shop') {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const cleanShop = shopUrl.replace('.myshopify.com', '');
      window.location.href = `${backendUrl}/api/shopify/auth?shop=${cleanShop}`;
      return;
    }

    // Mock connection for others (until Sprint 16/17) and for test Shopify
    await toggleSource({ 
      variables: { 
        platform: selectedPlatform, 
        connected: true 
      } 
    });
  };

  const currentPlatform = CONNECTOR_TYPES.find(p => p.id === selectedPlatform);

  return (
    <SidePanel
      isOpen={isOpen}
      onClose={handleClose}
      title={step === 'selection' ? t("title") : t("configTitle", { name: connectorData[selectedPlatform!]?.name })}
      subtitle={step === 'selection' ? t("subtitle") : t("configSubtitle")}
      footer={
        <div className="flex gap-3">
          {step === 'config' ? (
            <button
              onClick={() => { setStep('selection'); setError(null); }}
              className="flex-1 py-3 px-4 bg-white border border-slate-200 text-slate-600 rounded-lg text-[10px] font-bold hover:bg-slate-50 focus:ring-0 focus:outline-none transition-colors"
            >
              {tCommon('back')}
            </button>
          ) : (
            <button
              onClick={handleClose}
              className="flex-1 py-3 px-4 bg-white border border-slate-200 text-slate-600 rounded-xl text-[10px] font-bold hover:bg-slate-50 transition-colors"
            >
              {tCommon('cancel')}
            </button>
          )}
          
          {step === 'config' && (
            <button
              onClick={handleConnect}
              disabled={toggling || success}
              className={cn(
                "flex-[2] py-3 px-4 rounded-lg text-[10px] font-bold transition-all flex items-center justify-center gap-2 focus:ring-0 focus:outline-none",
                success 
                  ? "bg-emerald-500 text-white" 
                  : "bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-100 disabled:text-slate-400"
              )}
            >
              {toggling ? (
                <><Loader2 className="h-3.5 w-3.5 animate-spin" /> {t('connecting')}</>
              ) : success ? (
                <><CheckCircle2 className="h-3.5 w-3.5" /> {t('success')}</>
              ) : (
                <><Plus className="h-3.5 w-3.5" /> {t('connect')}</>
              )}
            </button>
          )}
        </div>
      }
    >
      <div className="p-4">
        {step === 'selection' ? (
          <div className="grid grid-cols-1 gap-3">
            {availablePlatforms.length === 0 ? (
              <div className="p-8 text-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
                <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto mb-3" />
                <p className="text-[10px] font-bold text-slate-900">{t('empty')}</p>
                <p className="text-[9px] text-slate-400 font-bold mt-1">{t('emptyDesc')}</p>
              </div>
            ) : (
              availablePlatforms.map((platform) => (
                <button
                  key={platform.id}
                  onClick={() => handleSelectPlatform(platform.id)}
                  className="group flex items-center gap-4 p-4 bg-white border border-slate-100 rounded-lg hover:border-primary/30 transition-all text-left"
                >
                  <div className={cn("p-3 rounded-lg transition-transform group-hover:scale-110", platform.bg)}>
                    <platform.icon className={cn("h-5 w-5", platform.color)} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-0.5">
                      <h3 className="text-[11px] font-black text-slate-900">{platform.name}</h3>
                      <ArrowRight className="h-3 w-3 text-slate-300 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </div>
                    <p className="text-[9px] text-slate-400 font-medium leading-relaxed">
                      {platform.description}
                    </p>
                  </div>
                </button>
              ))
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Platform Specific Forms */}
            {selectedPlatform === 'shopify' && (
              <div className="space-y-4">
                <div className="p-4 bg-emerald-50/50 rounded-lg border border-emerald-100/50 space-y-2">
                  <h4 className="text-[10px] font-bold text-emerald-700 flex items-center gap-2">
                    <Lock className="h-3 w-3" />
                    {t('shopify.title')}
                  </h4>
                  <p className="text-[9px] text-emerald-600/70 font-medium leading-relaxed">
                    {t('shopify.guide')}
                  </p>
                </div>
                
                <div className="space-y-2">
                  <label className="text-[10px] font-bold text-slate-400 ml-1">{t('shopify.label')}</label>
                  <div className="relative">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 p-1.5 bg-slate-50 rounded-lg group-focus-within:bg-emerald-50 transition-colors">
                      <Search className="h-3.5 w-3.5 text-slate-400 group-focus-within:text-emerald-600" />
                    </div>
                    <input 
                      type="text"
                      placeholder="ma-boutique-direct"
                      value={shopUrl}
                      onChange={(e) => setShopUrl(e.target.value)}
                      className="w-full h-12 pl-12 pr-32 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                      <span className="text-[9px] font-bold text-slate-400 tracking-tight">.myshopify.com</span>
                    </div>
                  </div>
                </div>

                <button 
                  type="button"
                  onClick={fillTestData}
                  className="w-full py-2 border border-dashed border-emerald-200 rounded-lg text-[9px] font-bold text-emerald-600 hover:bg-emerald-50 focus:ring-0 focus:outline-none transition-colors flex items-center justify-center gap-2"
                >
                  <Database className="h-3 w-3" />
                  {t('testData')}
                </button>
              </div>
            )}

            {selectedPlatform === 'amazon' && (
              <div className="space-y-4">
                <div className="p-4 bg-orange-50/50 rounded-lg border border-orange-100/50 space-y-2">
                  <h4 className="text-[10px] font-bold text-orange-700 flex items-center gap-2">
                    <ExternalLink className="h-3 w-3" />
                    {t('amazon.title')}
                  </h4>
                  <p className="text-[9px] text-orange-600/70 font-medium leading-relaxed">
                    {t('amazon.guide')}
                  </p>
                </div>
                
                <div className="grid grid-cols-1 gap-4">
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">Seller ID</label>
                    <input 
                      type="text"
                      placeholder="A123BCDEFGH456"
                      value={sellerId}
                      onChange={(e) => setSellerId(e.target.value)}
                      className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">MWS Auth Token</label>
                    <input 
                      type="password"
                      placeholder="amzn.mws.4ea07525-..."
                      value={mwsToken}
                      onChange={(e) => setMwsToken(e.target.value)}
                      className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                <button 
                  type="button"
                  onClick={fillTestData}
                  className="w-full py-2 border border-dashed border-orange-200 rounded-lg text-[9px] font-bold text-orange-600 hover:bg-orange-50 focus:ring-0 focus:outline-none transition-colors flex items-center justify-center gap-2"
                >
                  <Database className="h-3 w-3" />
                  {t('testData')}
                </button>
              </div>
            )}

            {selectedPlatform === 'woocommerce' && (
              <div className="space-y-4">
                <div className="p-4 bg-indigo-50/50 rounded-lg border border-indigo-100/50 space-y-2">
                  <h4 className="text-[10px] font-bold text-indigo-700 flex items-center gap-2">
                    <Database className="h-3 w-3" />
                    {t('woocommerce.title')}
                  </h4>
                  <p className="text-[9px] text-indigo-600/70 font-medium leading-relaxed">
                    {t('woocommerce.guide')}
                  </p>
                </div>
                
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">{t('woocommerce.url')}</label>
                    <input 
                      type="url"
                      placeholder="https://mon-site.com"
                      value={wooUrl}
                      onChange={(e) => setWooUrl(e.target.value)}
                      className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-400 ml-1">{t('woocommerce.key')}</label>
                      <input 
                        type="text"
                        placeholder="ck_..."
                        value={wooKey}
                        onChange={(e) => setWooKey(e.target.value)}
                        className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-slate-400 ml-1">{t('woocommerce.secret')}</label>
                      <input 
                        type="password"
                        placeholder="cs_..."
                        value={wooSecret}
                        onChange={(e) => setWooSecret(e.target.value)}
                        className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                      />
                    </div>
                  </div>
                </div>

                <button 
                  type="button"
                  onClick={fillTestData}
                  className="w-full py-2 border border-dashed border-indigo-200 rounded-lg text-[9px] font-bold text-indigo-600 hover:bg-indigo-50 focus:ring-0 focus:outline-none transition-colors flex items-center justify-center gap-2"
                >
                  <Database className="h-3 w-3" />
                  {t('testData')}
                </button>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-start gap-3 animate-in fade-in zoom-in duration-300">
                <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-red-700">{t('errors.title')}</p>
                  <p className="text-[9px] text-red-600 font-medium leading-relaxed">{error}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </SidePanel>
  );
}
