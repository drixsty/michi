'use client';

import React, { useState } from 'react';
import { useTranslations } from 'next-intl';
import { 
  Bell, 
  Mail, 
  Clock, 
  Calendar, 
  Shield, 
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ChevronRight,
  LayoutDashboard,
  Smartphone
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { CustomSelect } from '@/components/ui/CustomSelect';

export default function NotificationsPage() {
  const t = useTranslations('settings.notifications');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // States for report config
  const [reportsEnabled, setReportsEnabled] = useState(true);
  const [frequency, setFrequency] = useState('weekly');
  const [recipients, setRecipients] = useState('kevin@michi.app');

  const handleSave = async () => {
    setLoading(true);
    // Simulation API
    await new Promise(resolve => setTimeout(resolve, 1000));
    setLoading(false);
    setSuccess(true);
    setTimeout(() => setSuccess(false), 3000);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Notifications & rapports</h1>
        <p className="text-sm text-slate-500">
          Configurez la fréquence de vos rapports par email et vos alertes de stock.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Email Reports Section */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                <Mail className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Rapports périodiques</h3>
                <p className="text-[11px] text-slate-500 font-medium">Recevez un résumé de vos KPIs directement par email.</p>
              </div>
            </div>
            <button 
              onClick={() => setReportsEnabled(!reportsEnabled)}
              className={cn(
                "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none",
                reportsEnabled ? "bg-emerald-500" : "bg-slate-200"
              )}
            >
              <span className={cn(
                "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                reportsEnabled ? "translate-x-6" : "translate-x-1"
              )} />
            </button>
          </div>

          <div className={cn("p-6 space-y-6 transition-opacity", !reportsEnabled && "opacity-40 pointer-events-none")}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Fréquence d'envoi</label>
                <CustomSelect 
                  className="w-full h-11"
                  value={frequency}
                  onChange={setFrequency}
                  options={[
                    { value: 'daily', label: 'Journalier (Tous les matins)' },
                    { value: 'weekly', label: 'Hebdomadaire (Lundi matin)' },
                    { value: 'monthly', label: 'Mensuel (1er du mois)' }
                  ]}
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">Destinataires</label>
                <input 
                  type="email"
                  value={recipients}
                  onChange={(e) => setRecipients(e.target.value)}
                  className="w-full h-11 px-4 bg-slate-50 border border-slate-100 rounded-lg text-xs font-bold text-slate-900 focus:bg-white focus:border-primary/20 focus:ring-4 focus:ring-primary/5 focus:outline-none transition-all"
                  placeholder="admin@michi.app"
                />
              </div>
            </div>

            {/* Preview Card Mockup */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Aperçu du contenu</h4>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-[9px] font-bold">Premium</span>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white p-3 rounded-lg border border-slate-200/50 shadow-sm">
                  <div className="text-[9px] text-slate-400 font-bold mb-1">Ventes</div>
                  <div className="text-sm font-black text-slate-900">+12.5k€</div>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200/50 shadow-sm">
                  <div className="text-[9px] text-slate-400 font-bold mb-1">Stockout</div>
                  <div className="text-sm font-black text-red-600">8 refs</div>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200/50 shadow-sm">
                  <div className="text-[9px] text-slate-400 font-bold mb-1">Santé</div>
                  <div className="text-sm font-black text-emerald-600">98%</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Real-time Alerts Section */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
           <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-50 rounded-lg text-orange-600">
                  <Bell className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Alertes critiques</h3>
                  <p className="text-[11px] text-slate-500 font-medium">Soyez prévenu immédiatement en cas de rupture de stock imminente.</p>
                </div>
              </div>
           </div>
           
           <div className="space-y-4">
              <div className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer group">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                    <Smartphone className="h-4 w-4 text-slate-400" />
                  </div>
                  <span className="text-xs font-bold text-slate-700">Notifications Push (Mobile)</span>
                </div>
                <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-slate-400" />
              </div>
              <div className="flex items-center justify-between p-3 hover:bg-slate-50 rounded-lg transition-colors cursor-pointer group">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center">
                    <LayoutDashboard className="h-4 w-4 text-slate-400" />
                  </div>
                  <span className="text-xs font-bold text-slate-700">Alertes Dashboard</span>
                </div>
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              </div>
           </div>
        </div>
      </div>

      <div className="flex items-center justify-between pt-4">
        <p className="text-[10px] text-slate-400 font-medium italic">
          Les rapports sont envoyés à 08:00 (Fuseau horaire de l'organisation).
        </p>
        <button
          onClick={handleSave}
          disabled={loading}
          className={cn(
            "px-8 py-3 rounded-xl text-sm font-black transition-all shadow-lg flex items-center gap-2",
            success 
              ? "bg-emerald-500 text-white" 
              : "bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-100 disabled:text-slate-400"
          )}
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : (success ? <CheckCircle2 className="h-4 w-4" /> : "Enregistrer les réglages")}
        </button>
      </div>
    </div>
  );
}
