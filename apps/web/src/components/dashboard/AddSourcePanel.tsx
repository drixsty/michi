'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
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
import { CustomSelect } from '@/components/ui/CustomSelect';

// Reuse existing mutation from ConnectorsGrid (assuming it's compatible)
const TOGGLE_SOURCE = gql`
  mutation ToggleSource($platform: String!, $connected: Boolean!) {
    toggleSource(platform: $platform, connected: $connected) {
      id
      connected
    }
  }
`;

const UPDATE_STORE_CREDENTIALS = gql`
  mutation UpdateStoreCredentials($input: UpdateCredentialInput!) {
    updateStoreCredentials(input: $input) {
      id
      updatedAt
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
  },
  {
    id: 'csv',
    name: 'Fichier CSV',
    description: 'Importation manuelle via notre moteur d\'analyse intelligente IA.',
    icon: Database,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    status: 'Permanent'
  }
];

interface AddSourcePanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  connectedPlatforms: string[];
}

export function AddSourcePanel({ isOpen, onClose, onSuccess, connectedPlatforms }: AddSourcePanelProps) {
  const router = useRouter();
  const [step, setStep] = useState<'selection' | 'config'>('selection');
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  
  // Form states
  const [shopUrl, setShopUrl] = useState('');
  const [sellerId, setSellerId] = useState('');
  const [mwsToken, setMwsToken] = useState('');
  const [amazonRegion, setAmazonRegion] = useState('eu-west-1');
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
    },
    csv: {
      name: 'Fichier CSV',
      description: 'Importation manuelle via notre moteur d\'analyse intelligente IA.',
      icon: Database,
      color: 'text-blue-600',
      bg: 'bg-blue-50'
    }
  };

  const availablePlatforms = Object.keys(connectorData)
    .filter(id => id === 'csv' || !connectedPlatforms.some(cp => cp.toLowerCase() === id.toLowerCase()))
    .map(id => ({ id, ...connectorData[id] }));


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
    if (id === 'csv') {
      router.push('/dashboard/import');
      onClose();
      return;
    }
    setSelectedPlatform(id);
    setStep('config');
  };

  const fillTestData = () => {
    if (selectedPlatform === 'shopify') {
      setShopUrl('michi-test-shop');
      setMwsToken('shpat_test_token_123456789');
    }
    if (selectedPlatform === 'amazon') {
      setSellerId('A3TESTSELLERID');
      setMwsToken('Atzr|test_refresh_token_amzn_123');
      setAmazonRegion('eu-west-1');
    }
    if (selectedPlatform === 'woocommerce') {
      setWooUrl('https://michi-demo-store.com');
      setWooKey('ck_test_e5a2e5a2e5a2e5a2e5a2');
      setWooSecret('cs_test_f6b3f6b3f6b3f6b3f6b3');
    }
  };

  const [toggleSource, { loading: toggling }] = useMutation(TOGGLE_SOURCE);
  const [updateCredentials] = useMutation(UPDATE_STORE_CREDENTIALS);

  const handleConnect = async () => {
    if (!selectedPlatform) return;
    setError(null);
    
    try {
      // 1. Activer la source
      const { data: toggleData } = await toggleSource({ 
        variables: { 
          platform: selectedPlatform, 
          connected: true 
        } 
      });

      if (!toggleData?.toggleSource?.connected) {
        throw new Error("Failed to activate source");
      }

      // 2. Sauvegarder les credentials
      let apiKeyVal = "";
      let apiSecretVal = "";
      let meta = {};

      if (selectedPlatform === 'shopify') {
        apiKeyVal = shopUrl; // URL du shop dans apiKey (ou meta)
        apiSecretVal = mwsToken; 
        meta = { shop_url: shopUrl };
      } else if (selectedPlatform === 'amazon') {
        apiKeyVal = sellerId;
        apiSecretVal = mwsToken;
        meta = { seller_id: sellerId, region: amazonRegion };
      } else if (selectedPlatform === 'woocommerce') {
        apiKeyVal = wooKey;
        apiSecretVal = wooSecret;
        meta = { store_url: wooUrl };
      }

      await updateCredentials({
        variables: {
          input: {
            storeId: toggleData.toggleSource.id,
            apiKey: apiKeyVal || null,
            apiSecret: apiSecretVal || null,
            metaJson: JSON.stringify(meta)
          }
        }
      });

      setSuccess(true);
      setTimeout(() => {
        handleClose();
        onSuccess();
      }, 1500);

    } catch (err: any) {
      setError(err.message || "An error occurred during connection");
    }
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
                    Shopify configuration
                  </h4>
                  <p className="text-[9px] text-emerald-600/70 font-medium leading-relaxed">
                    Enter your shop URL and Admin Access Token from your Shopify custom app.
                  </p>
                </div>
                
                <div className="space-y-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">Shop URL</label>
                    <div className="relative">
                      <input 
                        type="text"
                        placeholder="my-store"
                        value={shopUrl}
                        onChange={(e) => setShopUrl(e.target.value)}
                        className="w-full h-11 pl-4 pr-32 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                      />
                      <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                        <span className="text-[9px] font-bold text-slate-400 tracking-tight">.myshopify.com</span>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">Admin access token</label>
                    <input 
                      type="password"
                      placeholder="shpat_xxxxxxxxxxxxxxxx"
                      value={mwsToken}
                      onChange={(e) => setMwsToken(e.target.value)}
                      className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                  </div>
                </div>

                <button 
                  type="button"
                  onClick={fillTestData}
                  className="w-full py-2 border border-dashed border-emerald-200 rounded-lg text-[9px] font-bold text-emerald-600 hover:bg-emerald-50 focus:ring-0 focus:outline-none transition-colors flex items-center justify-center gap-2"
                >
                  <Database className="h-3 w-3" />
                  Use test data
                </button>
              </div>
            )}

            {selectedPlatform === 'amazon' && (
              <div className="space-y-4">
                <div className="p-4 bg-orange-50/50 rounded-lg border border-orange-100/50 space-y-2">
                  <h4 className="text-[10px] font-bold text-orange-700 flex items-center gap-2">
                    <ExternalLink className="h-3 w-3" />
                    Amazon SP-API configuration
                  </h4>
                  <p className="text-[9px] text-orange-600/70 font-medium leading-relaxed">
                    Connect your Seller Central account using SP-API credentials.
                  </p>
                </div>
                
                <div className="grid grid-cols-1 gap-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">Seller ID</label>
                    <input 
                      type="text"
                      placeholder="A123BCDEFGH456"
                      value={sellerId}
                      onChange={(e) => setSellerId(e.target.value)}
                      className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">LWA refresh token</label>
                    <input 
                      type="password"
                      placeholder="Atzr|xxxxxxxxxxxxxxxx"
                      value={mwsToken}
                      onChange={(e) => setMwsToken(e.target.value)}
                      className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">Region</label>
                    <CustomSelect 
                      className="w-full h-11"
                      value={amazonRegion}
                      onChange={setAmazonRegion}
                      options={[
                        { value: 'eu-west-1', label: 'Europe (UK, FR, DE, ES, IT)' },
                        { value: 'us-east-1', label: 'North America (US, CA, MX, BR)' },
                        { value: 'us-west-2', label: 'Far East (AU, JP, SG)' }
                      ]}
                    />
                  </div>
                </div>

                <button 
                  type="button"
                  onClick={fillTestData}
                  className="w-full py-2 border border-dashed border-orange-200 rounded-lg text-[9px] font-bold text-orange-600 hover:bg-orange-50 focus:ring-0 focus:outline-none transition-colors flex items-center justify-center gap-2"
                >
                  <Database className="h-3 w-3" />
                  Use test data
                </button>
              </div>
            )}

            {selectedPlatform === 'woocommerce' && (
              <div className="space-y-4">
                <div className="p-4 bg-indigo-50/50 rounded-lg border border-indigo-100/50 space-y-2">
                  <h4 className="text-[10px] font-bold text-indigo-700 flex items-center gap-2">
                    <Database className="h-3 w-3" />
                    WooCommerce REST API
                  </h4>
                  <p className="text-[9px] text-indigo-600/70 font-medium leading-relaxed">
                    Generate Consumer Key and Secret in your WordPress settings.
                  </p>
                </div>
                
                <div className="space-y-3">
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 ml-1">Store URL</label>
                    <input 
                      type="url"
                      placeholder="https://my-site.com"
                      value={wooUrl}
                      onChange={(e) => setWooUrl(e.target.value)}
                      className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                    />
                  </div>
                  <div className="grid grid-cols-1 gap-3">
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-400 ml-1">Consumer key</label>
                      <input 
                        type="text"
                        placeholder="ck_xxxxxxxxxxxxxxxx"
                        value={wooKey}
                        onChange={(e) => setWooKey(e.target.value)}
                        className="w-full h-11 px-4 bg-slate-100/50 border border-transparent rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-[10px] font-bold text-slate-400 ml-1">Consumer secret</label>
                      <input 
                        type="password"
                        placeholder="cs_xxxxxxxxxxxxxxxx"
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
                  Use test data
                </button>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-100 rounded-xl flex items-start gap-3 animate-in fade-in zoom-in duration-300">
                <AlertCircle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-red-700">Connection error</p>
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
