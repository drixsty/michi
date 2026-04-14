'use client';

import React, { useState, useMemo } from 'react';
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  SortingState,
  getPaginationRowModel,
  getFilteredRowModel,
  RowSelectionState,
  ColumnFiltersState,
  ColumnSizingState,
} from '@tanstack/react-table';
import { Product, PlatformSource } from '@michi/types';
import { 
  ChevronRight, 
  ArrowUpDown,
  Search,
  ChevronLeft,
  Download,
  CheckCircle,
  Trash2,
  X,
  ShoppingCart,
  Globe,
  Anchor,
  Layers,
  ExternalLink
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { AnimatePresence, motion } from 'framer-motion';

const PLATFORM_ICONS: Record<PlatformSource, any> = {
  shopify: ShoppingCart,
  woocommerce: Globe,
  amazon: Anchor,
  csv: Layers,
  custom: Globe,
};

interface ProductTableProps {
  products: any[];
  query?: string;
  onRowClick?: (productId: string) => void;
}

export function ProductTable({ products, query = '', onRowClick }: ProductTableProps) {
  const router = useRouter();
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [channelFilter, setChannelFilter] = useState('all');
  const [columnSizing, setColumnSizing] = useState<ColumnSizingState>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('michi_column_sizing');
      return saved ? JSON.parse(saved) : {};
    }
    return {};
  });

  React.useEffect(() => {
    localStorage.setItem('michi_column_sizing', JSON.stringify(columnSizing));
  }, [columnSizing]);

  const filteredProducts = React.useMemo(() => {
    let result = products;
    
    // Search filter
    if (query) {
      const q = query.toLowerCase();
      result = result.filter(p => 
        p.title.toLowerCase().includes(q) || 
        p.sku.toLowerCase().includes(q)
      );
    }

    // Channel filter
    if (channelFilter !== 'all') {
      result = result.filter(p => {
        const channels = p.channels || [];
        return channels.some((c: any) => c.platform.toLowerCase() === channelFilter.toLowerCase());
      });
    }

    return result;
  }, [products, query, channelFilter]);

  const availablePlatforms = useMemo(() => {
    const platforms = new Set<string>();
    products.forEach(p => {
      (p.channels || []).forEach((c: any) => platforms.add(c.platform.toLowerCase()));
    });
    return Array.from(platforms);
  }, [products]);

  const columns: ColumnDef<any>[] = [
    {
      id: 'select',
      size: 40,
      minSize: 40,
      header: ({ table }) => (
        <div className="flex justify-center w-full">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-primary focus:ring-primary h-4 w-4"
            checked={table.getIsAllPageRowsSelected()}
            onChange={table.getToggleAllPageRowsSelectedHandler()}
          />
        </div>
      ),
      cell: ({ row }) => (
        <div className="flex justify-center w-full">
          <input
            type="checkbox"
            className="rounded border-gray-300 text-primary focus:ring-primary h-4 w-4"
            checked={row.getIsSelected()}
            onChange={row.getToggleSelectedHandler()}
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      ),
    },
    {
      accessorKey: 'title',
      size: 250,
      minSize: 150,
      header: ({ column }) => {
        return (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="flex items-center gap-1 text-foreground hover:text-foreground"
          >
            Produit unifié
            <ArrowUpDown className="h-3.5 w-3.5" />
          </button>
        )
      },
      cell: ({ row }) => {
        const stock = row.original.totalStock ?? row.original.currentStock;
        const threshold = row.original.warningThreshold ?? 10;
        return (
          <div className="flex items-center gap-2">
            <div className={cn(
              "h-1.5 w-1.5 rounded-full",
              stock === 0 ? "bg-red-500" : 
              stock <= threshold ? "bg-amber-400" : "bg-emerald-400"
            )} />
            <div className="flex flex-col">
              <span className="font-medium text-sentence">{row.original.title}</span>
              <span className="text-[10px] text-muted-foreground font-mono uppercase">{row.original.sku}</span>
            </div>
          </div>
        );
      },
    },
    {
      accessorKey: 'abcRank',
      header: ({ column }) => (
        <button 
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} 
          className="flex items-center mx-auto gap-1.5 text-slate-900 font-extrabold focus:outline-none"
        >
          ABC <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
        </button>
      ),
      size: 90,
      cell: ({ row }) => {
        const rank = row.original.abcRank ?? row.original.prediction?.abcRank ?? 'C';
        const styles: any = {
          'A': "bg-violet-50 text-violet-700 border-violet-200 shadow-sm shadow-violet-100",
          'B': "bg-blue-50 text-blue-700 border-blue-200",
          'C': "bg-slate-50 text-slate-600 border-slate-200",
        };
        
        return (
          <div className="flex justify-center">
            <span className={cn(
              "px-3 py-1 rounded-lg text-[11px] font-black border flex items-center gap-1.5 min-w-[34px] justify-center transition-all",
              styles[rank as keyof typeof styles] || styles['C']
            )}>
              {rank}
            </span>
          </div>
        );
      }
    },
    {
      id: 'sources',
      header: 'Sources',
      size: 100,
      cell: ({ row }) => {
        const channels = row.original.channels || [];
        const platforms = channels.length > 0 
          ? Array.from(new Set(channels.map((c: any) => c.platform.toLowerCase()))) 
          : ['shopify']; // Fallback for existing mock data before re-sync

        return (
          <div className="flex items-center justify-center gap-1.5">
            {platforms.map((platform: any, i) => {
              const Icon = PLATFORM_ICONS[platform as PlatformSource] || Globe;
              return (
                <div 
                  key={i} 
                  className="p-1.5 rounded-lg bg-slate-100 text-slate-500 hover:text-slate-900 transition-colors cursor-help"
                  title={platform}
                >
                  <Icon className="h-3.5 w-3.5" />
                </div>
              );
            })}
          </div>
        );
      }
    },
    {
      accessorKey: 'totalStock',
      size: 120,
      header: ({ column }) => (
        <button onClick={() => column.toggleSorting(column.getIsSorted() === "asc")} className="flex items-center mx-auto gap-1.5 text-slate-900 font-extrabold">
          Stock total <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
        </button>
      ),
      cell: ({ row }) => (
        <div className="text-center font-bold text-foreground">
          {row.original.totalStock ?? row.original.currentStock} u.
        </div>
      ),
    },
    {
      accessorKey: 'predictedStockoutDate',
      size: 150,
      header: 'Rupture prévue',
      cell: ({ row }) => {
        const dateStr = row.original.predictedStockoutDate || row.original.prediction?.predictedStockoutDate;
        if (!dateStr) return <div className="text-center"><span className="text-muted-foreground italic text-[10px]">Calcul...</span></div>;
        
        const predictedDate = new Date(dateStr);
        const today = new Date();
        const daysUntil = Math.max(0, Math.floor((predictedDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)));
        
        // Seuil dynamique : Urgent si daysUntil <= Lead Time (+ 3j buffer)
        const leadTime = row.original.leadTime || 14;
        const isUrgent = daysUntil <= (leadTime + 3);
        const isCritical = daysUntil <= 3;
        
        return (
          <div className="flex flex-col items-center">
            <span className={cn(
              "text-xs font-semibold px-2.5 py-1 rounded-md shadow-sm", 
              isCritical ? "bg-red-100 text-red-700 animate-pulse" :
              isUrgent ? "bg-red-50 text-red-600" : 
              "bg-amber-50 text-amber-600"
            )}>
              {predictedDate.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}
            </span>
            <span className="text-[9px] text-muted-foreground mt-1">
              J-{daysUntil}
            </span>
          </div>
        );
      },
    },
    {
      accessorKey: 'totalReorderQuantity',
      size: 120,
      header: 'À commander',
      cell: ({ row }) => {
        const qty = row.original.totalReorderQuantity || row.original.prediction?.reorderQuantity || 0;
        return (
          <div className="text-center">
            {qty > 0 ? (
              <span className="px-2.5 py-1 rounded-md bg-primary text-primary-foreground font-bold text-xs shadow-sm">
                +{Math.round(qty)} u.
              </span>
            ) : (
              <CheckCircle className="h-4 w-4 text-emerald-500 mx-auto" />
            )}
          </div>
        );
      },
    },
    {
      id: 'actions',
      size: 60,
      cell: ({ row }) => (
        <div className="flex justify-center">
          <button
            onClick={(e) => {
              e.stopPropagation();
              router.push(`/dashboard/product/${row.original.id || row.original.sku}`);
            }}
            className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-900 transition-all"
            title="Voir les détails complets"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        </div>
      )
    }
  ];

  const table = useReactTable({
    data: filteredProducts,
    columns,
    getCoreRowModel: getCoreRowModel(),
    onSortingChange: setSorting,
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onRowSelectionChange: setRowSelection,
    onColumnSizingChange: setColumnSizing,
    onColumnFiltersChange: setColumnFilters,
    columnResizeMode: 'onChange',
    state: {
      sorting,
      rowSelection,
      columnSizing,
      columnFilters,
    },
    initialState: {
      pagination: {
        pageSize: 10,
      },
    }
  });

  const selectedCount = Object.keys(rowSelection).length;

  return (
    <div className="relative space-y-4">
      {/* Table Headers & Global Filters */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-primary/5 rounded-lg">
             <Layers className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 data-testid="inventory-title" className="text-xs font-bold text-slate-900 tracking-tight">Catalogue Unifié</h3>
            <p className="text-[10px] text-slate-400 font-medium">{filteredProducts.length} produits affichés</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {availablePlatforms.length > 0 && (
             <div className="flex items-center gap-1 bg-slate-50 border border-slate-100 p-1 rounded-lg">
                <button 
                  onClick={() => setChannelFilter('all')}
                  className={cn(
                    "px-2 py-1 text-[9px] font-bold rounded-md transition-all",
                    channelFilter === 'all' ? "bg-white text-primary shadow-sm" : "text-slate-400 hover:text-slate-600"
                  )}
                >
                  Tous
                </button>
                {availablePlatforms.map(p => {
                  const Icon = PLATFORM_ICONS[p as PlatformSource] || Globe;
                  return (
                    <button 
                      key={p}
                      onClick={() => setChannelFilter(p)}
                      className={cn(
                        "flex items-center gap-1.5 px-2 py-1 text-[9px] font-bold rounded-md transition-all",
                        channelFilter === p ? "bg-white text-primary shadow-sm border-primary/10" : "text-slate-400 hover:text-slate-600"
                      )}
                    >
                      <Icon className="h-2.5 w-2.5" />
                      {p.charAt(0).toUpperCase() + p.slice(1)}
                    </button>
                  )
                })}
             </div>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-100 bg-white overflow-hidden shadow-none">
        <div className="overflow-x-auto no-scrollbar">
          <table className="w-full text-sm" style={{ tableLayout: 'fixed' }}>
            <thead className="bg-slate-100/50 border-b border-slate-200">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th 
                    key={header.id} 
                    className="px-4 py-4 text-left text-xs font-extrabold text-slate-900 tracking-widest border-b border-slate-200 relative group"
                    style={{ width: header.getSize() }}
                  >
                    <div className={cn(
                      "flex items-center",
                      header.column.id === 'sources' || header.column.id === 'predictedStockoutDate' || header.column.id === 'totalReorderQuantity' || header.column.id === 'totalStock' || header.column.id === 'abcRank' ? "justify-center" : 
                      header.column.id === 'actions' || header.column.id === 'select' ? "justify-center" : ""
                    )}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </div>
                    
                    {/* Resizer */}
                    <div
                      onMouseDown={header.getResizeHandler()}
                      onTouchStart={header.getResizeHandler()}
                      className={cn(
                        "absolute right-0 top-0 h-full w-1 cursor-col-resize select-none touch-none hover:bg-primary/30 transition-colors",
                        header.column.getIsResizing() ? "bg-primary w-1 opacity-100" : "opacity-0 group-hover:opacity-100"
                      )}
                    />
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y">
            {table.getRowModel().rows.length > 0 ? (
              table.getRowModel().rows.map((row) => (
                <tr 
                  key={row.id} 
                  className={cn(
                    "hover:bg-slate-50/50 transition-colors cursor-pointer",
                    row.getIsSelected() && "bg-primary/[0.02]"
                  )}
                  onClick={() => onRowClick?.(row.original.id || row.original.sku)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td 
                      key={cell.id} 
                      className="px-2 py-2"
                      style={{ width: cell.column.getSize() }}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="py-20 text-center">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <div className="p-3 bg-slate-50 rounded-full">
                       <Layers className="h-6 w-6 text-slate-300" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs font-bold text-slate-900 tracking-widest">Données vides</p>
                      <p className="text-[10px] text-slate-400 font-medium italic">Aucun produit ne correspond à votre sélection.</p>
                    </div>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-2">
        <div className="text-xs font-bold text-muted-foreground tracking-widest">
          {table.getState().pagination.pageIndex + 1} / {table.getPageCount()}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border bg-white text-muted-foreground disabled:opacity-50 hover:bg-accent transition-colors"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border bg-white text-muted-foreground disabled:opacity-50 hover:bg-accent transition-colors"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Floating Selection Action Bar */}
      <AnimatePresence>
        {selectedCount > 0 && (
          <motion.div 
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 w-full max-w-lg px-4"
          >
            <div className="bg-foreground text-background px-6 py-4 rounded-2xl shadow-2xl flex items-center justify-between border border-white/10 backdrop-blur-md bg-opacity-95">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center text-[10px] font-bold text-white">
                  {selectedCount}
                </div>
                <span className="text-xs font-bold tracking-tight">Actions groupées</span>
              </div>
              
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/10 transition-colors text-xs font-bold tracking-widest">
                  <Download className="h-3.5 w-3.5" />
                  Exporter
                </button>
                <button 
                  onClick={() => setRowSelection({})}
                  className="p-1.5 rounded-full hover:bg-white/10 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

