'use client';

import React from 'react';
import { Upload, Download } from 'lucide-react';

interface DashboardHeaderProps {
  title: string;
  subtitle: string;
  syncing: boolean;
  onSync: () => void;
  onExport: () => void;
  showActions?: boolean;
}

export function DashboardHeader({ 
  title, 
  subtitle, 
  syncing, 
  onSync, 
  onExport, 
  showActions = true
}: DashboardHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-5">
      <div>
        <h1 className="text-xl font-bold tracking-tight">{title}</h1>
        <p className="text-[11px] text-muted-foreground mt-0.5">{subtitle}</p>
      </div>
      {showActions && (
        <div className="flex items-center gap-2">
          <button
            onClick={onExport}
            data-testid="export-button"
            className="inline-flex h-9 items-center justify-center rounded-lg border border-input bg-background px-4 py-2 text-sm font-medium shadow-none transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <Download className="mr-2 h-4 w-4" />
            <span>Exporter</span>
          </button>
          <button
            onClick={onSync}
            disabled={syncing}
            data-testid="sync-button"
            className="inline-flex h-9 items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-none transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50"
          >
            <span>{syncing ? 'Synchronisation...' : 'Synchroniser'}</span>
          </button>
        </div>
      )}
    </div>
  );
}
