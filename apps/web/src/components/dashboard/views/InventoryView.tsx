'use client';

import React from 'react';
import { ProductTable } from '@/components/dashboard/ProductTable';
import { LoadingState } from '@/components/ui/LoadingState';
import type { OmnichannelProduct } from '@michi/types';

interface InventoryViewProps {
  loading: boolean;
  data: OmnichannelProduct[];
  searchQuery: string;
  onRowClick: (id: string) => void;
}

export const InventoryView: React.FC<InventoryViewProps> = ({ 
  loading, 
  data, 
  searchQuery, 
  onRowClick 
}) => {
  return (
    <div className="space-y-5 animate-in fade-in slide-in-from-bottom-2 duration-500">
      <div className="space-y-4">
        {loading && data.length === 0 ? (
          <LoadingState message="chargement du catalogue..." />
        ) : (
          <ProductTable 
            products={data} 
            query={searchQuery}
            onRowClick={onRowClick}
          />
        )}
      </div>
    </div>
  );
};
