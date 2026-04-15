'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Option {
  value: string;
  label: string;
}

interface CustomSelectProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  className?: string;
  placeholder?: string;
}

export function CustomSelect({ options, value, onChange, className, placeholder }: CustomSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  
  const selectedOption = options.find(opt => opt.value === value);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={cn("relative inline-block text-left min-w-[140px]", className)} ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full h-9 px-3 py-2 text-xs font-semibold text-foreground bg-white border border-border rounded-lg hover:border-primary/30 hover:bg-slate-50 transition-all focus:outline-none focus:ring-2 focus:ring-primary/10"
      >
        <span className="truncate">{selectedOption ? selectedOption.label : placeholder || 'Select...'}</span>
        <ChevronDown className={cn("ml-2 h-3.5 w-3.5 text-muted-foreground transition-transform duration-200", isOpen && "rotate-180")} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.98 }}
            animate={{ opacity: 1, y: 4, scale: 1 }}
            exit={{ opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute z-[100] w-full min-w-[160px] mt-1 bg-white border border-border rounded-xl shadow-xl shadow-slate-200/50 overflow-hidden"
          >
            <div className="py-1.5 max-h-64 overflow-y-auto no-scrollbar">
              {options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "flex items-center justify-between w-full px-3 py-2 text-[11px] font-medium transition-colors",
                    value === option.value 
                      ? "text-primary bg-primary/5" 
                      : "text-muted-foreground hover:text-foreground hover:bg-slate-50"
                  )}
                >
                  <span className="truncate">{option.label}</span>
                  {value === option.value && <Check className="h-3.5 w-3.5 text-primary" />}
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
