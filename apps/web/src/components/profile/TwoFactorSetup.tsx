'use client';

import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Shield, CheckCircle2, AlertCircle, Loader2, Copy, Download, RefreshCcw } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useMutation, gql } from '@apollo/client';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

const SETUP_2FA = gql`
  mutation Setup2FA {
    setup2fa {
      secret
      provisioningUri
    }
  }
`;

const CONFIRM_2FA = gql`
  mutation Confirm2FA($secret: String!, $code: String!) {
    confirm2fa(secret: $secret, code: $code) {
      success
      recoveryCodes
    }
  }
`;

const DISABLE_2FA = gql`
  mutation Disable2FA {
    disable2fa
  }
`;

interface TwoFactorSetupProps {
  isEnabled: boolean;
  onStatusChange: () => void;
}

export function TwoFactorSetup({ isEnabled, onStatusChange }: TwoFactorSetupProps) {
  const t = useTranslations('profile.twoFactor');
  const tCommon = useTranslations('common');
  const [isSettingUp, setIsSettingUp] = useState(false);
  const [code, setCode] = useState('');
  const [setupData, setSetupData] = useState<{ secret: string; uri: string } | null>(null);
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);

  const [generateSetup, { loading: loadingSetup }] = useMutation(SETUP_2FA, {
    onCompleted: (data) => {
      setSetupData({
        secret: data.setup2fa.secret,
        uri: data.setup2fa.provisioningUri
      });
      setIsSettingUp(true);
      setRecoveryCodes(null);
    },
    onError: (err) => {
      toast.error(err.message);
    }
  });

  const [confirmSetup, { loading: loadingConfirm }] = useMutation(CONFIRM_2FA, {
    onCompleted: (data) => {
      if (data.confirm2fa.success) {
        toast.success(t('successEnable'));
        setRecoveryCodes(data.confirm2fa.recoveryCodes);
        setIsSettingUp(false);
        setSetupData(null);
        onStatusChange();
      } else {
        toast.error(t('invalidCode'));
      }
    }
  });

  const [disable2fa, { loading: loadingDisable }] = useMutation(DISABLE_2FA, {
    onCompleted: (data) => {
      if (data.disable2fa) {
        toast.success(t('successDisable'));
        onStatusChange();
      }
    }
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success(tCommon('syncSuccess'));
  };

  const downloadRecoveryCodes = () => {
    if (!recoveryCodes) return;
    const content = `MICHI 道 - CODES DE SECOURS\n\nConservez ces codes en lieu sûr. Ils vous permettront d'accéder à votre compte si vous perdez votre téléphone.\nChaque code est à usage unique.\n\n${recoveryCodes.join('\n')}\n\nGénéré le : ${new Date().toLocaleString()}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'michi-recovery-codes.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  // STEP: RECOVERY CODES DISPLAY
  if (recoveryCodes) {
    return (
      <div className="bg-white rounded-lg border border-emerald-100 overflow-hidden animate-in zoom-in-95 duration-300">
        <div className="px-5 py-4 border-b border-emerald-50 bg-emerald-50/30 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-sm">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-[13px] font-bold text-emerald-900">Codes de secours générés</h2>
            <p className="text-[11px] text-emerald-700/70 font-medium">Sauvegardez-les précieusement avant de continuer.</p>
          </div>
        </div>
        
        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-3">
            {recoveryCodes.map((code, idx) => (
              <div key={idx} className="bg-muted/50 border border-border rounded-lg px-3 py-2 text-center font-mono text-sm font-bold text-foreground tracking-wider select-all">
                {code}
              </div>
            ))}
          </div>

          <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-[11px] text-amber-700 leading-relaxed font-medium">
              Ces codes sont l'unique moyen de récupérer votre compte si vous n'avez plus accès à votre application d'authentification. **Michi 道 ne pourra pas réinitialiser votre accès manuellement.**
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => copyToClipboard(recoveryCodes.join('\n'))}
              className="flex-1 h-10 border border-border rounded-lg text-[12px] font-bold text-muted-foreground hover:bg-muted transition-all flex items-center justify-center gap-2"
            >
              <Copy className="w-3.5 h-3.5" />
              Copier
            </button>
            <button
              onClick={downloadRecoveryCodes}
              className="flex-1 h-10 border border-border rounded-lg text-[12px] font-bold text-muted-foreground hover:bg-muted transition-all flex items-center justify-center gap-2"
            >
              <Download className="w-3.5 h-3.5" />
              Télécharger
            </button>
            <button
              onClick={() => setRecoveryCodes(null)}
              className="flex-[2] h-10 bg-foreground text-background rounded-lg text-[12px] font-bold hover:opacity-90 transition-all"
            >
              J'ai sauvegardé mes codes
            </button>
          </div>
        </div>
      </div>
    );
  }

  // STEP: QR CODE SCAN
  if (isSettingUp && setupData) {
    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
        <div className="bg-muted/30 p-6 rounded-lg border border-border flex flex-col items-center text-center">
          <div className="bg-white p-4 rounded-lg shadow-sm border border-border mb-4">
            <QRCodeSVG value={setupData.uri} size={180} level="M" />
          </div>
          <h4 className="text-sm font-bold text-foreground mb-2">{t('setupTitle')}</h4>
          <p className="text-xs text-muted-foreground max-w-xs">{t('setupDesc')}</p>
        </div>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-[12px] font-medium text-muted-foreground ml-0.5">
              {t('verifyCodeLabel')}
            </label>
            <input
              type="text"
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
              placeholder={t('verifyCodePlaceholder')}
              className="w-full h-10 bg-background border border-border rounded-lg px-4 text-center text-xl font-mono tracking-[0.5em] focus:ring-2 focus:ring-primary/10 focus:border-primary/20 outline-none transition-all"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setIsSettingUp(false)}
              className="flex-1 h-9 text-[12px] font-semibold text-muted-foreground hover:bg-muted rounded-lg transition-all"
            >
              {tCommon('cancel')}
            </button>
            <button
              onClick={() => confirmSetup({ variables: { secret: setupData.secret, code } })}
              disabled={code.length !== 6 || loadingConfirm}
              className="flex-[2] h-9 bg-foreground text-background rounded-lg text-[12px] font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            >
              {loadingConfirm && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {t('confirmButton')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // STEP: MAIN VIEW (ENABLED/DISABLED)
  return (
    <section className="bg-white rounded-lg border border-border overflow-hidden">
      <div className="px-5 py-4 border-b border-border bg-muted/20">
        <h2 className="text-[13px] font-semibold text-foreground">{t('title')}</h2>
      </div>
      
      <div className="p-5 flex items-center justify-between gap-4">
        <div className="flex gap-4">
          <div className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center shrink-0 transition-colors border",
            isEnabled 
              ? "bg-emerald-50 text-emerald-600 border-emerald-100" 
              : "bg-muted text-muted-foreground border-border"
          )}>
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <h3 className="text-sm font-semibold text-foreground">{t('title')}</h3>
              {isEnabled ? (
                <span className="flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-600 text-[10px] font-bold rounded border border-emerald-100 uppercase tracking-tight">
                  <CheckCircle2 className="w-2.5 h-2.5" />
                  {t('statusEnabled')}
                </span>
              ) : (
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-[10px] font-bold rounded border border-border uppercase tracking-tight">
                  {t('statusDisabled')}
                </span>
              )}
            </div>
            <p className="text-[13px] text-muted-foreground leading-relaxed max-w-md">
              {t('subtitle')}
            </p>
          </div>
        </div>

        <button
          onClick={() => isEnabled ? disable2fa() : generateSetup()}
          disabled={loadingSetup || loadingDisable}
          className={cn(
            "h-9 px-4 rounded-lg text-[12px] font-semibold transition-all flex items-center gap-2 shrink-0 border",
            isEnabled 
              ? "text-red-600 hover:bg-red-50 border-red-100" 
              : "bg-foreground text-background border-foreground hover:opacity-90"
          )}
        >
          {(loadingSetup || loadingDisable) && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          {isEnabled ? t('disableButton') : t('enableButton')}
        </button>
      </div>
    </section>
  );
}
