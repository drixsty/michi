'use client';

import React, { useState, useRef } from 'react';
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';
import {
  GET_OMNICHANNEL_INVENTORY,
  EXPORT_REPLENISHMENT_CSV,
  INGEST_WOOCOMMERCE_DATA,
} from '@/graphql/queries/getOmnichannelInventory';
import type { OmnichannelProduct, PlatformSource } from '@/types/product';
import {
  Download,
  Upload,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Layers,
  CheckCircle2,
} from 'lucide-react';

// ── Platform badge ─────────────────────────────────────────────────────────────

const PLATFORM_CONFIG: Record<PlatformSource, { label: string; bg: string; text: string }> = {
  shopify: { label: 'Shopify', bg: 'bg-green-50', text: 'text-green-700' },
  woocommerce: { label: 'WooCommerce', bg: 'bg-purple-50', text: 'text-purple-700' },
  amazon: { label: 'Amazon', bg: 'bg-orange-50', text: 'text-orange-700' },
  csv: { label: 'CSV', bg: 'bg-sky-50', text: 'text-sky-700' },
  custom: { label: 'Custom', bg: 'bg-gray-50', text: 'text-gray-600' },
};

function PlatformBadge({ platform }: { platform: PlatformSource }) {
  const cfg = PLATFORM_CONFIG[platform] ?? PLATFORM_CONFIG.custom;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-bold tracking-tight ${cfg.bg} ${cfg.text}`}
    >
      {cfg.label}
    </span>
  );
}

// ── Stock risk badge ───────────────────────────────────────────────────────────

function StockRiskBadge({ product }: { product: OmnichannelProduct }) {
  if (product.hasConflict) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-red-50 text-red-700 ring-1 ring-red-200">
        <AlertTriangle size={11} />
        Conflit cross-canal
      </span>
    );
  }
  const days = product.dominantRunRate > 0
    ? Math.floor(product.totalStock / product.dominantRunRate)
    : null;

  if (days !== null && days < 14) {
    return (
      <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-50 text-amber-700 ring-1 ring-amber-200">
        {days}j restants
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">
      {product.totalStock} u.
    </span>
  );
}

// ── Expandable row ─────────────────────────────────────────────────────────────

function OmnichannelRow({ product }: { product: OmnichannelProduct }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className={`border-b border-gray-100 transition-colors hover:bg-gray-50/60 cursor-pointer ${
          product.hasConflict ? 'bg-red-50/30' : ''
        }`}
        onClick={() => setExpanded((v) => !v)}
      >
        {/* Expand icon */}
        <td className="pl-4 py-3 w-8">
          {product.channelCount > 1 ? (
            expanded ? (
              <ChevronDown size={14} className="text-gray-400" />
            ) : (
              <ChevronRight size={14} className="text-gray-400" />
            )
          ) : null}
        </td>

        {/* SKU + titre */}
        <td className="py-3 pr-4">
          <div className="flex flex-col gap-0.5">
            <span className="text-xs font-mono text-gray-400">{product.sku}</span>
            <span className="text-sm font-semibold text-gray-800 leading-tight">
              {product.title}
            </span>
          </div>
        </td>

        {/* Canal(aux) */}
        <td className="py-3 pr-4">
          <div className="flex flex-wrap gap-1">
            {product.channels.map((ch, i) => (
              <PlatformBadge key={i} platform={ch.platform} />
            ))}
          </div>
        </td>

        {/* Stock total */}
        <td className="py-3 pr-4 text-right">
          <StockRiskBadge product={product} />
        </td>

        {/* Run rate */}
        <td className="py-3 pr-4 text-right text-sm text-gray-500 tabular-nums">
          {product.dominantRunRate > 0 ? `${product.dominantRunRate.toFixed(1)} u/j` : '—'}
        </td>

        {/* Rupture prévisionnelle */}
        <td className="py-3 pr-4 text-right text-sm text-gray-500">
          {product.predictedStockoutDate
            ? new Date(product.predictedStockoutDate).toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
              })
            : '—'}
        </td>

        {/* Qté à commander */}
        <td className="py-3 pr-6 text-right">
          {product.totalReorderQuantity > 0 ? (
            <span className="text-sm font-bold text-violet-600">
              +{product.totalReorderQuantity}
            </span>
          ) : (
            <CheckCircle2 size={15} className="text-emerald-400 ml-auto" />
          )}
        </td>
      </tr>

      {/* Expanded: détail par canal */}
      {expanded && product.channelCount > 1 && (
        product.channels.map((ch, i) => (
          <tr key={i} className="bg-gray-50/80 border-b border-gray-100/60">
            <td />
            <td colSpan={2} className="py-2 pl-8 text-xs text-gray-500">
              <PlatformBadge platform={ch.platform} />
            </td>
            <td className="py-2 text-right text-xs font-semibold text-gray-700 tabular-nums pr-4">
              {ch.currentStock} u.
            </td>
            <td className="py-2 text-right text-xs text-gray-400 tabular-nums pr-4">
              LT {ch.leadTime}j
            </td>
            <td className="py-2 text-right text-xs text-gray-400 tabular-nums pr-4">
              MOQ {ch.moq}
            </td>
            <td />
          </tr>
        ))
      )}
    </>
  );
}

// ── WooCommerce import modal ───────────────────────────────────────────────────

function WooCommerceImportModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [productsCsv, setProductsCsv] = useState('');
  const [ordersCsv, setOrdersCsv] = useState('');
  const [ingest, { loading, error }] = useMutation(INGEST_WOOCOMMERCE_DATA);
  const productsRef = useRef<HTMLInputElement>(null);
  const ordersRef = useRef<HTMLInputElement>(null);

  const handleFile = (
    e: React.ChangeEvent<HTMLInputElement>,
    setter: (v: string) => void,
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setter((ev.target?.result as string) ?? '');
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!productsCsv) return;
    await ingest({ variables: { productsCsv, ordersCsv: ordersCsv || undefined } });
    onSuccess();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white rounded-3xl shadow-2xl p-8 w-full max-w-md flex flex-col gap-5">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Importer WooCommerce</h2>
          <p className="text-sm text-gray-500 mt-1">
            Exportez vos données depuis wp-admin → Produits → Exporter et wp-admin → Commandes → Exporter.
          </p>
        </div>

        {/* Products CSV */}
        <div>
          <label className="text-xs font-bold uppercase tracking-widest text-gray-400 block mb-2">
            Fichier Produits (obligatoire)
          </label>
          <div
            className="border-2 border-dashed border-gray-200 rounded-2xl p-4 text-center cursor-pointer hover:border-violet-300 transition-colors"
            onClick={() => productsRef.current?.click()}
          >
            <Upload size={20} className="mx-auto text-gray-300 mb-2" />
            <p className="text-xs text-gray-400">
              {productsCsv ? '✅ Fichier chargé' : 'Cliquez pour sélectionner le CSV produits WooCommerce'}
            </p>
          </div>
          <input
            ref={productsRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => handleFile(e, setProductsCsv)}
          />
        </div>

        {/* Orders CSV */}
        <div>
          <label className="text-xs font-bold uppercase tracking-widest text-gray-400 block mb-2">
            Fichier Commandes (optionnel — historique ventes)
          </label>
          <div
            className="border-2 border-dashed border-gray-200 rounded-2xl p-4 text-center cursor-pointer hover:border-violet-300 transition-colors"
            onClick={() => ordersRef.current?.click()}
          >
            <Upload size={20} className="mx-auto text-gray-300 mb-2" />
            <p className="text-xs text-gray-400">
              {ordersCsv ? '✅ Fichier chargé' : 'Cliquez pour sélectionner le CSV commandes WooCommerce'}
            </p>
          </div>
          <input
            ref={ordersRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => handleFile(e, setOrdersCsv)}
          />
        </div>

        {error && (
          <p className="text-xs text-red-600 bg-red-50 rounded-xl px-3 py-2">{error.message}</p>
        )}

        <div className="flex gap-3 pt-2">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 rounded-2xl text-sm font-semibold text-gray-500 bg-gray-100 hover:bg-gray-200 transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleImport}
            disabled={!productsCsv || loading}
            className="flex-1 py-2.5 rounded-2xl text-sm font-bold text-white bg-violet-600 hover:bg-violet-700 disabled:opacity-40 transition-colors"
          >
            {loading ? 'Import en cours…' : 'Importer'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function OmnichannelView() {
  const [wooModal, setWooModal] = useState(false);
  const [platformFilter, setPlatformFilter] = useState<PlatformSource | 'all'>('all');

  const { data, loading, error, refetch } = useQuery(GET_OMNICHANNEL_INVENTORY, {
    fetchPolicy: 'cache-and-network',
  });

  const [exportCsv, { loading: exporting }] = useLazyQuery(EXPORT_REPLENISHMENT_CSV, {
    fetchPolicy: 'no-cache',
    onCompleted: (data) => {
      // Déclencher le téléchargement côté navigateur
      const blob = new Blob([data.exportReplenishmentCsv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `michi-reappro-${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  const products: OmnichannelProduct[] = data?.omnichannelInventory ?? [];

  const platforms = Array.from(
    new Set(products.flatMap((p) => p.channels.map((c) => c.platform)))
  ) as PlatformSource[];

  const filtered = platformFilter === 'all'
    ? products
    : products.filter((p) => p.channels.some((c) => c.platform === platformFilter));

  const conflictCount = products.filter((p) => p.hasConflict).length;
  const multiChannelCount = products.filter((p) => p.channelCount > 1).length;

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-gray-400">
        Chargement de l&apos;inventaire omnichannel…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-48 text-sm text-red-500">
        Erreur : {error.message}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* ── KPI strip ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block">SKUs unifiés</span>
          <span className="text-3xl font-bold text-gray-900">{products.length}</span>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block">Multi-canal</span>
          <span className="text-3xl font-bold text-violet-600">{multiChannelCount}</span>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block">Conflits</span>
          <span className={`text-3xl font-bold ${conflictCount > 0 ? 'text-red-600' : 'text-emerald-500'}`}>
            {conflictCount}
          </span>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
          <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 block">Plateformes</span>
          <span className="text-3xl font-bold text-gray-900">{platforms.length}</span>
        </div>
      </div>

      {/* ── Toolbar ───────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Platform filter tabs */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setPlatformFilter('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
              platformFilter === 'all'
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
          >
            <Layers size={12} className="inline mr-1" />
            Tous
          </button>
          {platforms.map((p) => {
            const cfg = PLATFORM_CONFIG[p];
            return (
              <button
                key={p}
                onClick={() => setPlatformFilter(p)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors ${
                  platformFilter === p
                    ? 'bg-gray-900 text-white'
                    : `${cfg.bg} ${cfg.text} hover:opacity-80`
                }`}
              >
                {cfg.label}
              </button>
            );
          })}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setWooModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-bold text-purple-700 bg-purple-50 hover:bg-purple-100 transition-colors"
          >
            <Upload size={13} />
            Import WooCommerce
          </button>
          <button
            onClick={() => exportCsv()}
            disabled={exporting || products.length === 0}
            className="flex items-center gap-2 px-4 py-2 rounded-2xl text-xs font-bold text-violet-700 bg-violet-50 hover:bg-violet-100 disabled:opacity-40 transition-colors"
          >
            <Download size={13} />
            {exporting ? 'Export…' : 'Export Réappro CSV'}
          </button>
        </div>
      </div>

      {/* ── Table ─────────────────────────────────────────────────────────── */}
      {filtered.length === 0 ? (
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-12 text-center">
          <Layers size={40} className="mx-auto text-gray-200 mb-4" />
          <p className="text-sm font-semibold text-gray-500">
            Aucun produit trouvé pour ce filtre.
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Synchronisez vos données ou importez un CSV WooCommerce.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60">
                <th className="pl-4 py-3 w-8" />
                <th className="py-3 pr-4 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                  Produit
                </th>
                <th className="py-3 pr-4 text-[10px] font-bold uppercase tracking-widest text-gray-400">
                  Canaux
                </th>
                <th className="py-3 pr-4 text-[10px] font-bold uppercase tracking-widest text-gray-400 text-right">
                  Stock total
                </th>
                <th className="py-3 pr-4 text-[10px] font-bold uppercase tracking-widest text-gray-400 text-right">
                  Run rate
                </th>
                <th className="py-3 pr-4 text-[10px] font-bold uppercase tracking-widest text-gray-400 text-right">
                  Rupture prévue
                </th>
                <th className="py-3 pr-6 text-[10px] font-bold uppercase tracking-widest text-gray-400 text-right">
                  À commander
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((product) => (
                <OmnichannelRow key={product.sku} product={product} />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── WooCommerce import modal ───────────────────────────────────────── */}
      {wooModal && (
        <WooCommerceImportModal
          onClose={() => setWooModal(false)}
          onSuccess={() => refetch()}
        />
      )}
    </div>
  );
}
