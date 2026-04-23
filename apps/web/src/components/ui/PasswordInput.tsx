'use client';

import React, { useState } from 'react';
import { Eye, EyeOff, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';

interface PasswordInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ className, label, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const tAuth = useTranslations('auth.login');

    const togglePasswordVisibility = () => {
      setShowPassword(!showPassword);
    };

    return (
      <div className="space-y-1">
        {label && (
          <label className="text-[11px] font-bold text-foreground/60 ml-1">
            {label}
          </label>
        )}
        <div className="relative group">
          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 group-focus-within:text-primary transition-colors" />
          <input
            {...props}
            type={showPassword ? 'text' : 'password'}
            ref={ref}
            className={cn(
              "w-full h-11 pl-10 pr-10 rounded-md border bg-background text-sm transition-all focus:outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary/20 border-border",
              className
            )}
          />
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/40 hover:text-foreground transition-colors focus:outline-none"
            title={showPassword ? tAuth('hidePassword') : tAuth('showPassword')}
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    );
  }
);

PasswordInput.displayName = 'PasswordInput';
