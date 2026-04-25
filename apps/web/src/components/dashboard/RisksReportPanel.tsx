'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle, ShoppingCart, Check, Loader2 } from 'lucide-react';
import { createPortal } from 'react-dom';
import { useMutation, gql } from '@apollo/client';
import { cn } from '@/lib/utils';
import { CanDo } from '@/components/auth/CanDo';
import { Permission } from '@/hooks/usePermissions';

const CREATE_PURCHASE_ORDER = gql`
  mutation CreatePurchaseOrder($productId: ID!, $supplierId: ID!, $quantity: Int!) {
    createPurchaseOrder(productId: $productId, supplierId: $supplierId, quantity: $quantity) {
      id
      status
    }
  }
`;

interface Risk {
  productId: string;
  sku: string;
  title: string;
  riskValue: number;
  stockoutDate: string;
  reorderQuantity?: number;
  daysOfStock?: number;
  supplierId?: string;
  costPrice?: number;
}

interface RisksReportPanelProps {
  isOpen: boolean;
  onClose: () => void;
  risks: Risk[];
  formatCurrency: (val: number) => string;
  onSelectProduct: (productId: string) => void;
}

export function RisksReportPanel({ 
  isOpen, 
  onClose, 
  risks, 
  formatCurrency,
  onSelectProduct 
}: RisksReportPanelProps) {
  const [mounted, setMounted] = React.useState(false);
  const [orderedIds, setOrderedIds] = React.useState<Set<string>>(new Set());
  const [orderingId, setOrderingId] = React.useState<string | null>(null);

  const [createPO] = useMutation(CREATE_PURCHASE_ORDER);

  React.useEffect(() => setMounted(true), []);

  const handleOrder = async (risk: Risk, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!risk.supplierId || !risk.reorderQuantity) return;
    
    setOrderingId(risk.productId);
    try {
      await createPO({
        variables: {
          productId: risk.productId,
          supplierId: risk.supplierId,
          quantity: risk.reorderQuantity,
        }
      });
      setOrderedIds(prev => new Set(prev).add(risk.productId));
    } catch (err) {
      console.error('Erreur PO:', err);
    } finally {
      setOrderingId(null);
    }
  };

  const getUrgencyBadge = (daysOfStock?: number) => {
    if (!daysOfStock || daysOfStock <= 7) return { label: 'Critique', className: 'bg-red-50 text-red-600 border-red-100' };
    if (daysOfStock <= 21) return { label: 'Urgent', className: 'bg-amber-50 text-amber-600 border-amber-100' };
    return { label: 'À surveiller', className: 'bg-blue-50 text-blue-600 border-blue-100' };
  };

  // Budget total estimé
  const totalBudget = risks.reduce((acc, r) => acc + (r.reorderQuantity || 0) * (r.costPrice || 0), 0);

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[60] bg-slate-900/20 backdrop-blur-md"
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 right-0 z-[70] w-full max-w-2xl bg-white border-l border-slate-100 flex flex-col shadow-none"
          >
            {/* Header */}
            <div className="p-5 border-b border-slate-50 flex items-center justify-between sticky top-0 bg-white z-10">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 bg-red-50 rounded-lg">
                    <AlertTriangle className="h-4 w-4 text-red-500" />
                  </div>
                  <h2 className="text-sm font-black text-slate-900 tracking-widest">Rapport des risques financiers</h2>
                </div>
                <p className="text-[10px] font-medium text-slate-400">{risks.length} produits nécessitant un réapprovisionnement.</p>
              </div>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-slate-50 rounded-full transition-colors"
              >
                <X className="h-4 w-4 text-slate-400" />
              </button>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-y-auto p-0 scrollbar-thin scrollbar-thumb-slate-200">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-slate-50 border-b border-slate-100 z-10">
                  <tr>
                    <th className="px-5 py-2.5 text-[10px] font-bold text-slate-400 tracking-widest">Produit</th>
                    <th className="px-3 py-2.5 text-[10px] font-bold text-slate-400 tracking-widest text-right">Risque</th>
                    <th className="px-3 py-2.5 text-[10px] font-bold text-slate-400 tracking-widest text-center">Qté recommandée</th>
                    <th className="px-3 py-2.5 text-[10px] font-bold text-slate-400 tracking-widest text-center">Urgence</th>
                    <th className="px-3 py-2.5 text-[10px] font-bold text-slate-400 tracking-widest text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {risks.map((risk, i) => {
                    const urgency = getUrgencyBadge(risk.daysOfStock);
                    const isOrdered = orderedIds.has(risk.productId);
                    const isOrdering = orderingId === risk.productId;

                    return (
                      <tr 
                        key={i} 
                        className="group hover:bg-slate-50/50 transition-colors cursor-pointer"
                        onClick={() => onSelectProduct(risk.productId)}
                      >
                        <td className="px-5 py-3">
                          <div className="space-y-0.5">
                            <p className="text-xs font-bold text-slate-900 group-hover:text-primary transition-colors">{risk.title}</p>
                            <p className="text-[9px] font-bold text-slate-400 tracking-tighter uppercase">{risk.sku}</p>
                          </div>
                        </td>
                        <td className="px-3 py-3 text-right">
                          <span className="text-[10px] font-black text-red-600">
                            {formatCurrency(risk.riskValue)}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-center">
                          <span className="text-xs font-black text-indigo-600">
                            {risk.reorderQuantity || '—'}
                          </span>
                          <span className="text-[8px] font-medium text-slate-400 ml-1">u.</span>
                        </td>
                        <td className="px-3 py-3 text-center">
                          <span className={cn("text-[8px] font-bold px-2 py-0.5 rounded-full border", urgency.className)}>
                            {urgency.label}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-center">
                          {isOrdered ? (
                            <span className="inline-flex items-center gap-1 text-[9px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg">
                              <Check className="h-3 w-3" /> Commandé
                            </span>
                          ) : risk.supplierId && risk.reorderQuantity ? (
                            <CanDo permission={Permission.INVENTORY_EDIT} fallback={<span className="text-[8px] text-slate-300 italic">Lecture seule</span>}>
                              <button
                                onClick={(e) => handleOrder(risk, e)}
                                disabled={isOrdering}
                                className="inline-flex items-center gap-1 text-[9px] font-bold text-white bg-slate-900 hover:bg-slate-800 px-2.5 py-1 rounded-lg transition-colors disabled:opacity-50"
                              >
                                {isOrdering ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <><ShoppingCart className="h-3 w-3" /> Commander</>
                                )}
                              </button>
                            </CanDo>
                          ) : (
                            <span className="text-[8px] text-slate-300 italic">N/A</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              
              {risks.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 text-center opacity-30">
                  <AlertTriangle className="h-12 w-12 mb-4" />
                  <p className="text-xs font-bold">Aucun risque financier détecté.</p>
                </div>
              )}
            </div>

            {/* Footer Summary */}
            <div className="p-5 bg-slate-50 border-t border-slate-100 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-400 tracking-widest">Total impact 30j</span>
                <span className="text-lg font-black text-red-600">
                  {formatCurrency(risks.reduce((acc, r) => acc + r.riskValue, 0))}
                </span>
              </div>
              {totalBudget > 0 && (
                <div className="flex items-center justify-between p-3 bg-indigo-50 rounded-xl border border-indigo-100">
                  <div>
                    <p className="text-[10px] font-bold text-indigo-600">Budget de réapprovisionnement estimé</p>
                    <p className="text-[8px] text-indigo-500 italic">Basé sur les quantités IA × coût d'achat unitaire</p>
                  </div>
                  <span className="text-lg font-black text-indigo-700">
                    {formatCurrency(totalBudget)}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
