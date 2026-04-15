'use client';

import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Bell, AlertTriangle, AlertCircle, Info, CheckCircle2, Trash2, ExternalLink } from 'lucide-react';
import Link from 'next/link';
import { useQuery, useMutation, gql } from '@apollo/client';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import { cn } from '@/lib/utils';
import { LoadingState } from '../ui/LoadingState';
import { useStore } from '@/context/StoreContext';

const GET_UNREAD_ALERTS = gql`
  query GetUnreadAlerts {
    unreadAlerts {
      id
      type
      message
      severity
      createdAt
      isRead
      productId
    }
  }
`;

const DELETE_ALERT = gql`
  mutation DeleteAlert($id: ID!) {
    deleteAlert(alertId: $id)
  }
`;


interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationPanel({ isOpen, onClose }: NotificationPanelProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const { user, currentOrganization } = useStore();
  
  const { data, loading, refetch } = useQuery(GET_UNREAD_ALERTS, {
    skip: !isOpen || !user || !currentOrganization,
    pollInterval: 30000,
  });

  const [deleteAlert] = useMutation(DELETE_ALERT, {
    onCompleted: () => refetch(),
  });

  const alerts = data?.unreadAlerts || [];

  const getIcon = (type: string) => {
    switch (type) {
      case 'STOCKOUT_CRITICAL':
      case 'CRITICAL_STOCK': 
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'STOCKOUT_RISK_HIGH':
      case 'STOCKOUT_RISK': 
        return <AlertCircle className="h-5 w-5 text-orange-500" />;
      case 'STOCKOUT_WARNING':
        return <Bell className="h-5 w-5 text-amber-500" />;
      default: 
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const panelContent = (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-md z-[60]"
          />

          {/* Side Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-screen w-full max-w-md bg-white shadow-2xl z-[70] flex flex-col border-l border-slate-200 rounded-tl-xl"
            data-testid="notification-panel"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b sticky top-0 bg-white z-20">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/5 rounded-lg">
                    <Bell className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900 lowercase">notifications</h2>
                    <p className="text-[10px] text-slate-400 font-medium lowercase tracking-wide">suivi des stocks en temps réel</p>
                  </div>
                </div>
                <button 
                  onClick={onClose}
                  className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                >
                  <X className="h-5 w-5 text-slate-400" />
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto no-scrollbar p-4 space-y-3 bg-white">
              {loading ? (
                <LoadingState className="h-64" message="chargement..." />
              ) : alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-4 px-8">
                  <div className="w-16 h-16 rounded-3xl bg-slate-50 flex items-center justify-center text-slate-300">
                     <CheckCircle2 className="h-8 w-8" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-slate-900 font-semibold">Tout est sous contrôle</p>
                    <p className="text-sm text-slate-500">Aucune alerte critique pour le moment.</p>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {alerts.map((alert: any) => (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="group relative flex items-center gap-4 px-4 py-3 transition-colors cursor-pointer border-b border-white/50 rounded-lg hover:bg-slate-50"
                    >
                      {/* Severity Dot & Icon */}
                      <div className="relative shrink-0 flex items-center justify-center">
                        <div className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center bg-white/50 text-slate-400 group-hover:bg-white transition-colors",
                          (alert.type === 'CRITICAL_STOCK' || alert.type === 'STOCKOUT_CRITICAL') && "text-red-500",
                          (alert.type === 'STOCKOUT_RISK' || alert.type === 'STOCKOUT_RISK_HIGH') && "text-orange-500",
                          alert.type === 'STOCKOUT_WARNING' && "text-amber-500"
                        )}>
                          {getIcon(alert.type)}
                        </div>
                        {(alert.type === 'CRITICAL_STOCK' || alert.type === 'STOCKOUT_CRITICAL') && (
                          <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white shadow-sm" />
                        )}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <p className="text-[10px] font-medium text-slate-400 whitespace-nowrap">
                            {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true, locale: fr })}
                          </p>
                        </div>
                        <p className="text-xs text-slate-600 leading-snug font-medium lowercase break-words">
                          {alert.message.replace(/^(alerte|danger|attention)\s*:\s*/i, '').toLowerCase()}
                        </p>
                      </div>

                      {/* Action Overlays (Hover) - Fixed Positioning */}
                      <div className="shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200 transform translate-x-2 group-hover:translate-x-0">
                         <Link 
                            href={`/dashboard/product/${alert.productId}`}
                            onClick={onClose}
                            className="h-8 w-8 flex items-center justify-center bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-primary hover:border-primary/30 transition-all shadow-sm"
                            title="ouvrir"
                         >
                            <ExternalLink className="h-4 w-4" />
                         </Link>
                         <button
                            onClick={() => deleteAlert({ variables: { id: alert.id } })}
                            className="h-8 w-8 flex items-center justify-center bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-red-500 hover:border-red-200 transition-all shadow-sm"
                            title="supprimer"
                         >
                            <Trash2 className="h-4 w-4" />
                         </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {alerts.length > 0 && (
              <div className="p-4 bg-slate-50 border-t">
                <button 
                  onClick={onClose}
                  className="w-full h-11 bg-white border border-slate-200 text-slate-600 rounded-xl text-sm font-bold hover:bg-slate-100 transition-all active:scale-[0.98] lowercase"
                >
                  fermer
                </button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );

  if (!mounted) return null;

  return createPortal(panelContent, document.body);
}
