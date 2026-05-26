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
import { PlatformSource } from '@michi/types';
import {
  ChevronRight,
  ArrowUpDown,
  ChevronLeft,
  Download,
  CheckCircle,
  X,
  ShoppingCart,
  Globe,
  Anchor,
  Layers,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Activity,
  Info,
  Clock,
  Check,
  ChevronDown
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { useQuery, useMutation, gql } from '@apollo/client';
import { UPDATE_PRODUCT_SETTINGS } from '@/graphql/mutations/updateProduct';

const GET_SUPPLIERS = gql`
  query GetSuppliers {
    suppliers {
      id
      name
    }
  }
`;


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
  const t = useTranslations('inventory.table');
  const tInventory = useTranslations('inventory');
  const tCommon = useTranslations('common');
  const router = useRouter();

  const [isLeadTimeModalOpen, setIsLeadTimeModalOpen] = useState(false);
  const [isSupplierModalOpen, setIsSupplierModalOpen] = useState(false);
  const [newLeadTime, setNewLeadTime] = useState('');
  const [selectedSupplierId, setSelectedSupplierId] = useState('');
  const [isSupplierDropdownOpen, setIsSupplierDropdownOpen] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const [updateProduct] = useMutation(UPDATE_PRODUCT_SETTINGS);
  const { data: suppliersData } = useQuery(GET_SUPPLIERS);
  
  const suppliers = suppliersData?.suppliers || [];

  const selectedSupplierName = useMemo(() => {
    if (!selectedSupplierId) return "Choisir un fournisseur";
    if (selectedSupplierId === "null") return "Aucun (désassigner)";
    const found = suppliers.find((s: any) => s.id === selectedSupplierId);
    return found ? found.name : "Choisir un fournisseur";
  }, [selectedSupplierId, suppliers]);

  const handleExportSelected = () => {
    try {
      const selectedRows = table.getSelectedRowModel().rows.map(r => r.original);
      if (selectedRows.length === 0) return;
      
      const headers = ['Produit', 'SKU', 'Stock Actuel', 'ABC', 'Délai Fournisseur (jours)', 'MOQ', 'Date de Rupture Prévisible', 'Quantité de Réapprovisionnement'];
      const rows = selectedRows.map(p => {
        const stock = p.totalStock ?? p.currentStock ?? 0;
        const rank = p.abcRank ?? p.prediction?.abcRank ?? 'C';
        const lead = p.leadTime ?? 14;
        const moq = p.moq ?? 0;
        const dateStr = p.predictedStockoutDate ?? p.prediction?.predictedStockoutDate ?? '—';
        const qty = p.totalReorderQuantity ?? p.prediction?.reorderQuantity ?? 0;
        return [
          `"${p.title.replace(/"/g, '""')}"`,
          p.sku,
          stock,
          rank,
          lead,
          moq,
          dateStr,
          Math.round(qty)
        ];
      });
      const csvContent = [headers, ...rows].map(e => e.join(',')).join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `michi_bulk_export_${new Date().toISOString().slice(0,10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Export error", err);
    }
  };

  const handleApplyLeadTime = async () => {
    if (!newLeadTime) return;
    setIsUpdating(true);
    try {
      const selectedProductIds = table.getSelectedRowModel().rows.map(r => r.original.id);
      
      await Promise.all(
        selectedProductIds.map(productId =>
          updateProduct({
            variables: {
              id: productId,
              leadTime: parseInt(newLeadTime)
            }
          })
        )
      );
      
      setIsLeadTimeModalOpen(false);
      setNewLeadTime('');
      setRowSelection({});
      router.refresh();
    } catch (err) {
      console.error("Failed to update lead times", err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleApplySupplier = async () => {
    setIsUpdating(true);
    try {
      const selectedProductIds = table.getSelectedRowModel().rows.map(r => r.original.id);
      
      const supplierIdParam = selectedSupplierId === 'null' ? null : selectedSupplierId;
      
      await Promise.all(
        selectedProductIds.map(productId =>
          updateProduct({
            variables: {
              id: productId,
              supplierId: supplierIdParam
            }
          })
        )
      );
      
      setIsSupplierModalOpen(false);
      setSelectedSupplierId('');
      setRowSelection({});
      router.refresh();
    } catch (err) {
      console.error("Failed to update suppliers", err);
    } finally {
      setIsUpdating(false);
    }
  };
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

    if (query) {
      const q = query.toLowerCase();
      result = result.filter(p =>
        p.title.toLowerCase().includes(q) ||
        p.sku.toLowerCase().includes(q)
      );
    }

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
      header: ({ table }) => {
        const isAllSelected = table.getIsAllPageRowsSelected();
        const isSomeSelected = table.getIsSomePageRowsSelected();
        return (
          <div className="flex justify-center w-full">
            <button
              onClick={table.getToggleAllPageRowsSelectedHandler()}
              className={cn(
                "h-4 w-4 shrink-0 rounded border transition-all flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary/40 cursor-pointer",
                isAllSelected
                  ? "bg-primary border-primary text-white"
                  : isSomeSelected
                  ? "bg-primary/50 border-primary text-white"
                  : "bg-white border-slate-300 hover:border-slate-400 text-transparent"
              )}
              aria-label="Sélectionner tous les produits"
            >
              {(isAllSelected || isSomeSelected) && <Check className="h-3 w-3 stroke-[3]" />}
            </button>
          </div>
        );
      },
      cell: ({ row }) => {
        const isSelected = row.getIsSelected();
        return (
          <div className="flex justify-center w-full">
            <button
              onClick={(e) => {
                e.stopPropagation();
                row.toggleSelected(!isSelected);
              }}
              className={cn(
                "h-4 w-4 shrink-0 rounded border transition-all flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary/40 cursor-pointer",
                isSelected
                  ? "bg-primary border-primary text-white"
                  : "bg-white border-slate-300 hover:border-slate-400 text-transparent"
              )}
              aria-label="Sélectionner le produit"
            >
              {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
            </button>
          </div>
        );
      },
    },
    {
      accessorKey: 'title',
      size: 250,
      minSize: 150,
      header: ({ column }) => (
        <button
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="flex items-center gap-1 text-foreground hover:text-foreground"
        >
          {t('product')}
          <ArrowUpDown className="h-3.5 w-3.5" />
        </button>
      ),
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
      accessorKey: 'volatility',
      size: 110,
      header: ({ column }) => (
        <div className="flex items-center justify-center gap-1.5 text-slate-900 font-extrabold cursor-help group">
          {t('volatility')}
          <Info className="h-3 w-3 text-slate-300 group-hover:text-primary transition-colors" />
        </div>
      ),
      cell: ({ row }) => {
        const rr = row.original.dominantRunRate ?? row.original.runRate ?? row.original.prediction?.runRate ?? 0;
        const sigma = row.original.demandSigma ?? row.original.prediction?.demandSigma ?? 0;
        
        if (rr <= 0) return <div className="text-center text-muted-foreground text-[10px]">—</div>;
        
        const cv = sigma / rr;
        
        let label = tInventory('volatility.stable');
        let colorClass = "bg-emerald-50 text-emerald-700 border-emerald-100";
        let Icon = ShieldCheck;
        
        if (cv > 0.5) {
          label = tInventory('volatility.high');
          colorClass = "bg-red-50 text-red-700 border-red-100";
          Icon = Activity;
        } else if (cv > 0.2) {
          label = tInventory('volatility.moderate');
          colorClass = "bg-amber-50 text-amber-700 border-amber-100";
          Icon = Zap;
        }
        
        return (
          <div className="flex justify-center">
            <span className={cn(
              "px-2 py-0.5 rounded-lg text-[9px] font-bold border flex items-center gap-1 transition-all",
              colorClass
            )}>
              <Icon className="h-2.5 w-2.5" />
              {label}
            </span>
          </div>
        );
      }
    },
    {
      id: 'reliability',
      size: 110,
      header: ({ column }) => (
        <div className="flex items-center justify-center gap-1.5 text-slate-900 font-extrabold cursor-help group">
          {t('reliability')}
          <Info className="h-3 w-3 text-slate-300 group-hover:text-primary transition-colors" />
        </div>
      ),
      cell: ({ row }) => {
        const score = row.original.supplier?.reliabilityScore ?? 1.0;
        const avgDelay = row.original.supplier?.averageDelayDays ?? 0;
        
        let label = tInventory('reliability.stable');
        let colorClass = "bg-emerald-50 text-emerald-700 border-emerald-100";
        let Icon = ShieldCheck;
        
        if (score < 0.7 || avgDelay > 5) {
          label = tInventory('reliability.unstable');
          colorClass = "bg-red-50 text-red-700 border-red-100";
          Icon = ShieldAlert;
        } else if (score < 0.9 || avgDelay > 2) {
          label = tInventory('reliability.moderate');
          colorClass = "bg-amber-50 text-amber-700 border-amber-100";
          Icon = Clock;
        }
        
        return (
          <div className="flex justify-center">
            <span className={cn(
              "px-2 py-0.5 rounded-lg text-[9px] font-bold border flex items-center gap-1 transition-all",
              colorClass
            )}>
              <Icon className="h-2.5 w-2.5" />
              {label}
            </span>
          </div>
        );
      }
    },
    {
      id: 'sources',
      header: t('sources'),
      size: 100,
      cell: ({ row }) => {
        const channels = row.original.channels || [];
        const platforms = Array.from(new Set(channels.map((c: any) => c.platform.toLowerCase())));
        if (platforms.length === 0) {
          return <div className="text-center text-muted-foreground text-[10px]">—</div>;
        }
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
          {t('stock')} <ArrowUpDown className="h-3.5 w-3.5 text-slate-400" />
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
      header: t('stockout'),
      cell: ({ row }) => {
        const dateStr = row.original.predictedStockoutDate || row.original.prediction?.predictedStockoutDate;
        if (!dateStr) return <div className="text-center"><span className="text-muted-foreground italic text-[10px]">{tInventory('volatility.calculating')}</span></div>;

        const predictedDate = new Date(dateStr);
        const today = new Date();
        const daysUntil = Math.max(0, Math.floor((predictedDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)));

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
              {predictedDate.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
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
      header: t('reorder'),
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

  // ─── Mobile Card View ───────────────────────────────────────────────────────
  const MobileCardView = () => (
    <div className="space-y-2">
      {filteredProducts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <div className="p-3 bg-slate-50 rounded-full">
            <Layers className="h-6 w-6 text-slate-300" />
          </div>
          <div className="text-center space-y-1">
            <p className="text-xs font-bold text-slate-900 tracking-widest">{tCommon('emptyTitle')}</p>
            <p className="text-[10px] text-slate-400 italic">{tInventory('emptySubtitle')}</p>
          </div>
        </div>
      ) : (
        filteredProducts.map((p) => {
          const stock = p.totalStock ?? p.currentStock;
          const threshold = p.warningThreshold ?? 10;
          const isCritical = stock === 0;
          const isWarning = !isCritical && stock <= threshold;
          const rank = p.abcRank ?? p.prediction?.abcRank ?? 'C';
          const dateStr = p.predictedStockoutDate ?? p.prediction?.predictedStockoutDate;
          const qty = p.totalReorderQuantity ?? p.prediction?.reorderQuantity ?? 0;

          const rankStyles: Record<string, string> = {
            A: 'bg-violet-50 text-violet-700 border-violet-200',
            B: 'bg-blue-50 text-blue-700 border-blue-200',
            C: 'bg-slate-50 text-slate-600 border-slate-200',
          };

          return (
            <div
              key={p.id ?? p.sku}
              onClick={() => onRowClick?.(p.id ?? p.sku)}
              className="bg-white border border-slate-100 rounded-xl p-4 space-y-3 active:bg-slate-50 transition-colors cursor-pointer shadow-sm"
            >
              {/* Top row: name + ABC badge */}
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <div className={cn(
                      "h-2 w-2 rounded-full shrink-0",
                      isCritical ? "bg-red-500" : isWarning ? "bg-amber-400" : "bg-emerald-400"
                    )} />
                    <p className="text-sm font-semibold text-slate-900 truncate">{p.title}</p>
                  </div>
                  <p className="text-[10px] text-muted-foreground font-mono uppercase ml-3.5">{p.sku}</p>
                </div>
                <span className={cn(
                  "px-2 py-0.5 rounded-md text-[10px] font-black border shrink-0",
                  rankStyles[rank] ?? rankStyles.C
                )}>
                  {rank}
                </span>
              </div>

              {/* Mid row: stock + stockout + reorder */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-slate-50 rounded-lg py-2 px-1">
                  <p className={cn(
                    "text-base font-bold",
                    isCritical ? "text-red-500" : isWarning ? "text-amber-500" : "text-slate-800"
                  )}>
                    {stock}
                  </p>
                  <p className="text-[9px] text-muted-foreground font-medium mt-0.5">{t('stock')}</p>
                </div>
                <div className="bg-slate-50 rounded-lg py-2 px-1">
                  {dateStr ? (
                    <>
                      <p className="text-[11px] font-bold text-amber-600">
                        {new Date(dateStr).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })}
                      </p>
                      <p className="text-[9px] text-muted-foreground font-medium mt-0.5">{t('stockout')}</p>
                    </>
                  ) : (
                    <>
                      <p className="text-[11px] text-muted-foreground">—</p>
                      <p className="text-[9px] text-muted-foreground font-medium mt-0.5">{t('stockout')}</p>
                    </>
                  )}
                </div>
                <div className="bg-slate-50 rounded-lg py-2 px-1">
                  {qty > 0 ? (
                    <>
                      <p className="text-[11px] font-bold text-primary">+{Math.round(qty)}</p>
                      <p className="text-[9px] text-muted-foreground font-medium mt-0.5">{t('reorder')}</p>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-500 mx-auto" />
                      <p className="text-[9px] text-muted-foreground font-medium mt-0.5">{t('reorder')}</p>
                    </>
                  )}
                </div>
              </div>

              {/* Bottom row: sources + open button */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  {Array.from(new Set((p.channels || []).map((c: any) => c.platform.toLowerCase()))).map((platform: any, i) => {
                    const Icon = PLATFORM_ICONS[platform as PlatformSource] || Globe;
                    return (
                      <div key={i} className="p-1.5 rounded-md bg-slate-100 text-slate-500">
                        <Icon className="h-3 w-3" />
                      </div>
                    );
                  })}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    router.push(`/dashboard/product/${p.id ?? p.sku}`);
                  }}
                  className="flex items-center gap-1.5 px-3 py-2 text-[11px] font-bold text-primary bg-primary/5 hover:bg-primary/10 rounded-lg transition-colors min-h-[36px]"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  {tCommon('open')}
                </button>
              </div>
            </div>
          );
        })
      )}
    </div>
  );

  return (
    <div className="relative space-y-4">
      {/* Table Headers & Global Filters */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-primary/5 rounded-lg">
            <Layers className="h-4 w-4 text-primary" />
          </div>
          <div>
            <h3 data-testid="inventory-title" className="text-xs font-bold text-slate-900 tracking-tight">{t('catalogTitle')}</h3>
            <p className="text-[10px] text-slate-400 font-medium">{filteredProducts.length} {t('productsShown')}</p>
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
                {tInventory('all')}
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

      {/* Mobile card view */}
      <div className="md:hidden">
        <MobileCardView />
      </div>

      {/* Desktop table view */}
      <div className="hidden md:block rounded-xl border border-slate-100 bg-white overflow-hidden shadow-none">
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
                         header.column.id === 'sources' || header.column.id === 'predictedStockoutDate' || header.column.id === 'totalReorderQuantity' || header.column.id === 'totalStock' || header.column.id === 'abcRank' || header.column.id === 'volatility' || header.column.id === 'reliability' ? "justify-center" :
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
                        <p className="text-xs font-bold text-slate-900 tracking-widest">{tCommon('emptyTitle')}</p>
                        <p className="text-[10px] text-slate-400 font-medium italic">{tInventory('emptySubtitle')}</p>
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination — desktop only (mobile has all cards at once) */}
      <div className="hidden md:flex items-center justify-between px-2">
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
            className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 w-full max-w-xl px-4"
          >
            <div className="bg-slate-950/95 text-white pl-5 pr-4 py-3.5 rounded-2xl shadow-2xl flex items-center justify-between border border-white/10 backdrop-blur-md">
              <div className="flex items-center gap-3 shrink-0">
                <div className="h-6 w-6 rounded-full bg-primary flex items-center justify-center text-[10px] font-bold text-white shrink-0 shadow-lg shadow-primary/20">
                  {selectedCount}
                </div>
                <span className="text-xs font-bold tracking-tight whitespace-nowrap text-white">
                  {t('groupedActions')}
                </span>
              </div>
 
              <div className="flex items-center gap-2.5 shrink-0">
                <button
                  onClick={() => setIsLeadTimeModalOpen(true)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 active:scale-[0.98] transition-all text-[10px] font-bold tracking-widest text-slate-200 border border-white/5"
                >
                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                  Délais
                </button>
                <button
                  onClick={() => setIsSupplierModalOpen(true)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 active:scale-[0.98] transition-all text-[10px] font-bold tracking-widest text-slate-200 border border-white/5"
                >
                  <Layers className="h-3.5 w-3.5 text-slate-400" />
                  Fournisseur
                </button>
                <button
                  onClick={handleExportSelected}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary hover:bg-primary/90 text-white active:scale-[0.98] transition-all text-[10px] font-black tracking-widest shadow-md shadow-primary/20"
                >
                  <Download className="h-3.5 w-3.5" />
                  {tCommon('export')}
                </button>
                <div className="w-[1px] h-5 bg-white/10 mx-0.5" />
                <button
                  onClick={() => setRowSelection({})}
                  className="p-1.5 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-all active:scale-95 shrink-0"
                  title="Annuler la sélection"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Lead Time Batch Modal */}
      <AnimatePresence>
        {isLeadTimeModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-950 border border-white/10 text-white rounded-2xl p-6 w-full max-w-sm shadow-2xl flex flex-col gap-4"
            >
              <div className="flex justify-between items-center border-b border-white/10 pb-3">
                <h3 className="text-sm font-bold tracking-tight text-white">Mettre à jour les délais</h3>
                <button
                  onClick={() => setIsLeadTimeModalOpen(false)}
                  className="p-1 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] tracking-wider text-slate-400 font-bold block mb-1">
                  Délai de livraison du fournisseur (en jours)
                </label>
                <input
                  type="number"
                  placeholder="Ex. 14"
                  value={newLeadTime}
                  onChange={(e) => setNewLeadTime(e.target.value)}
                  className="w-full bg-zinc-900/80 border border-white/10 hover:border-white/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary text-white transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                  min="0"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setIsLeadTimeModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold hover:bg-white/5 transition-colors border border-white/10 text-slate-300"
                >
                  Annuler
                </button>
                <button
                  onClick={handleApplyLeadTime}
                  disabled={isUpdating || !newLeadTime}
                  className="bg-primary hover:bg-primary/90 text-white px-5 py-2 rounded-xl text-xs font-bold transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[100px]"
                >
                  {isUpdating ? 'En cours...' : 'Appliquer'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
 
      {/* Supplier Batch Modal */}
      <AnimatePresence>
        {isSupplierModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/60 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-950 border border-white/10 text-white rounded-2xl p-6 w-full max-w-sm shadow-2xl flex flex-col gap-4"
            >
              <div className="flex justify-between items-center border-b border-white/10 pb-3">
                <h3 className="text-sm font-bold tracking-tight text-white">Mettre à jour le fournisseur</h3>
                <button
                  onClick={() => setIsSupplierModalOpen(false)}
                  className="p-1 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="space-y-1">
                <label className="text-[10px] tracking-wider text-slate-400 font-bold block mb-1">
                  Sélectionner le fournisseur
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setIsSupplierDropdownOpen(!isSupplierDropdownOpen)}
                    className="w-full flex items-center justify-between bg-zinc-900/80 border border-white/10 hover:border-white/20 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary text-white transition-all cursor-pointer text-left"
                  >
                    <span className={cn(
                      !selectedSupplierId ? "text-slate-400" : "text-white"
                    )}>
                      {selectedSupplierName}
                    </span>
                    <ChevronDown 
                      className="h-4 w-4 text-slate-400 shrink-0 transition-transform duration-200" 
                      style={{ transform: isSupplierDropdownOpen ? 'rotate(180deg)' : 'none' }} 
                    />
                  </button>

                  <AnimatePresence>
                    {isSupplierDropdownOpen && (
                      <>
                        <div 
                          className="fixed inset-0 z-30" 
                          onClick={() => setIsSupplierDropdownOpen(false)} 
                        />
                        <motion.div
                          initial={{ opacity: 0, y: -4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                          transition={{ duration: 0.15 }}
                          className="absolute left-0 right-0 mt-2 z-40 max-h-60 overflow-y-auto rounded-xl border border-white/10 bg-zinc-950/95 backdrop-blur-md shadow-2xl p-1.5 scrollbar-thin scrollbar-thumb-white/10"
                        >
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedSupplierId("");
                              setIsSupplierDropdownOpen(false);
                            }}
                            className={cn(
                              "w-full text-left px-3 py-2 text-sm rounded-lg transition-all flex items-center justify-between cursor-pointer",
                              !selectedSupplierId 
                                ? "bg-primary/10 text-primary font-medium" 
                                : "text-slate-400 hover:text-white hover:bg-white/5"
                            )}
                          >
                            <span>Choisir un fournisseur</span>
                            {!selectedSupplierId && <Check className="h-3.5 w-3.5" />}
                          </button>
                          
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedSupplierId("null");
                              setIsSupplierDropdownOpen(false);
                            }}
                            className={cn(
                              "w-full text-left px-3 py-2 text-sm rounded-lg transition-all flex items-center justify-between cursor-pointer",
                              selectedSupplierId === "null" 
                                ? "bg-primary/10 text-primary font-medium" 
                                : "text-slate-300 hover:text-white hover:bg-white/5"
                            )}
                          >
                            <span>Aucun (désassigner)</span>
                            {selectedSupplierId === "null" && <Check className="h-3.5 w-3.5" />}
                          </button>

                          {suppliers.length > 0 && (
                            <div className="h-[1px] bg-white/5 my-1" />
                          )}

                          {suppliers.map((s: any) => {
                            const isCurrent = selectedSupplierId === s.id;
                            return (
                              <button
                                key={s.id}
                                type="button"
                                onClick={() => {
                                  setSelectedSupplierId(s.id);
                                  setIsSupplierDropdownOpen(false);
                                }}
                                className={cn(
                                  "w-full text-left px-3 py-2 text-sm rounded-lg transition-all flex items-center justify-between cursor-pointer",
                                  isCurrent 
                                    ? "bg-primary/10 text-primary font-medium" 
                                    : "text-slate-300 hover:text-white hover:bg-white/5"
                                )}
                              >
                                <span className="truncate">{s.name}</span>
                                {isCurrent && <Check className="h-3.5 w-3.5" />}
                              </button>
                            );
                          })}
                        </motion.div>
                      </>
                    )}
                  </AnimatePresence>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setIsSupplierModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold hover:bg-white/5 transition-colors border border-white/10 text-slate-300"
                >
                  Annuler
                </button>
                <button
                  onClick={handleApplySupplier}
                  disabled={isUpdating || !selectedSupplierId}
                  className="bg-primary hover:bg-primary/90 text-white px-5 py-2 rounded-xl text-xs font-bold transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[100px]"
                >
                  {isUpdating ? 'En cours...' : 'Appliquer'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
