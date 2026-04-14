'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  message?: string;
  fullScreen?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: { container: 'w-8 h-8 rounded-lg', spinner: 'w-4 h-4 border-2' },
  md: { container: 'w-12 h-12 rounded-xl', spinner: 'w-6 h-6 border-2' },
  lg: { container: 'w-16 h-16 rounded-2xl', spinner: 'w-8 h-8 border-[3px]' },
};

export function LoadingState({ 
  message, 
  fullScreen = false, 
  size = 'md',
  className 
}: LoadingStateProps) {
  const { container, spinner } = sizeClasses[size];

  return (
    <div className={cn(
      "flex flex-col items-center justify-center space-y-4 animate-in fade-in duration-500",
      fullScreen ? "min-h-[60vh]" : "py-12",
      className
    )}>
      <div className="relative">
        <div className={cn(
          "bg-primary/10 flex items-center justify-center animate-pulse",
          container
        )}>
           <div className={cn(
             "border-primary/30 border-t-primary rounded-full animate-spin",
             spinner
           )} />
        </div>
      </div>
      {message && (
        <p className="text-[10px] font-bold text-slate-400 tracking-widest uppercase opacity-50 lowercase">
          {message}
        </p>
      )}
    </div>
  );
}
