'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';

interface SidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: string;
}

export function SidePanel({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  maxWidth = 'max-w-md'
}: SidePanelProps) {
  // Client-side portal target check
  const [mounted, setMounted] = React.useState(false);
  React.useEffect(() => setMounted(true), []);

  if (!mounted) return null;

  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[60] bg-slate-900/20 backdrop-blur-md"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={cn(
              "fixed inset-y-0 right-0 z-[70] w-full bg-white border-l border-slate-100 flex flex-col shadow-none",
              maxWidth
            )}
          >
            {/* Header */}
            <div className="p-4 border-b border-slate-50 flex items-start justify-between sticky top-0 bg-white z-10">
              <div className="space-y-1">
                {title && (
                  <h2 className="text-sm font-extrabold text-slate-900">{title}</h2>
                )}
                {subtitle && (
                  <p className="text-[10px] font-bold text-slate-400">{subtitle}</p>
                )}
              </div>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-slate-50 rounded-full transition-colors"
                aria-label="Fermer"
              >
                <X className="h-4 w-4 text-slate-400" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto no-scrollbar p-0">
              {children}
            </div>

            {/* Footer */}
            {footer && (
              <div className="p-4 border-t border-slate-50 bg-slate-50/30">
                {footer}
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  );
}
