'use client';

import React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, icon, ...props }, ref) => {
    return (
      <div className="space-y-1 w-full text-left">
        {label && (
          <label className="text-[11px] font-bold text-foreground/60 ml-1">
            {label}
          </label>
        )}
        <div className="relative group">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 group-focus-within:text-primary transition-colors">
              {icon}
            </div>
          )}
          <input
            {...props}
            ref={ref}
            className={cn(
              "w-full h-11 rounded-md border bg-background text-sm transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-border px-4",
              icon && "pl-10",
              className
            )}
          />
        </div>
      </div>
    );
  }
);

Input.displayName = 'Input';
