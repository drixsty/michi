'use client';

import React, { useState, useRef } from 'react';
import { 
  Upload, FileText, CheckCircle2, AlertCircle, 
  ChevronRight, ArrowLeft, ArrowRight, Table as TableIcon,
  Search, Database, Sparkles, MoveHorizontal, Loader2,
  Package, TrendingUp
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQuery, gql } from '@apollo/client';
import { useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';

import { LoadingOverlay } from '@/components/ui/LoadingOverlay';
import { CustomSelect } from '@/components/ui/CustomSelect';
import { PermissionGuard } from '@/components/auth/PermissionGuard';
import { Permission } from '@/hooks/usePermissions';

import { SMART_IMPORT } from '@/graphql/mutations/ingestCSV';

const GET_SOURCES = gql`
  query GetSources {
    sources {
      id
      name
      platform
      connected
    }
  }
`;

const ANALYZE_CSV = gql`
  mutation AnalyzeCsv($csvContent: String!) {
    analyzeCsv(csvContent: $csvContent) {
      columns
      columnTypes
      suggestedMapping {
        targetField
        csvColumn
        confidence
      }
      sampleData
      anomalies
    }
  }
`;

// --- Types ---

import { ColumnMapping, ImportStep, CSVAnalysis, SmartImportResult } from '@/types/import';

// --- Page Component ---

export default function SmartImportPage() {
  const t = useTranslations('import');
  const router = useRouter();
  const [step, setStep] = useState<ImportStep>('upload');
  const [fileName, setFileName] = useState<string | null>(null);
  const [csvContent, setCsvContent] = useState<string>('');
  const [analysis, setAnalysis] = useState<CSVAnalysis | null>(null);
  const [mapping, setMapping] = useState<ColumnMapping>({ sku: '', title: '', stock: '' });
  const [importResult, setImportResult] = useState<SmartImportResult | null>(null);
  const [selectedStoreId, setSelectedStoreId] = useState<string>('other');

  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: sourcesData } = useQuery(GET_SOURCES, {
    onCompleted: (data) => {
      // On reste sur 'other' par défaut comme défini dans le state initial
    }
  });

  const [analyzeCsv, { loading: analyzing }] = useMutation(ANALYZE_CSV);
  const [smartImport, { loading: importing }] = useMutation(SMART_IMPORT);

  // --- Handlers ---

  const storeOptions = [
    ...(sourcesData?.sources
      ?.filter((s: any) => s.platform !== 'CSV')
      .map((s: any) => ({
        value: s.id,
        label: s.name
      })) || []),
    { value: 'other', label: t('destination.other') }
  ];

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!selectedStoreId) {
      alert(t('destination.choose'));
      return;
    }

    setFileName(file.name);
    const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
    const reader = new FileReader();
    
    reader.onload = async (event) => {
      const content = event.target?.result as string;
      setCsvContent(content);
      
      try {
        const { data } = await analyzeCsv({ variables: { csvContent: content } });
        if (data?.analyzeCsv) {
          setAnalysis(data.analyzeCsv);
          
          const initialMapping: any = {};
          data.analyzeCsv.suggestedMapping.forEach((s: any) => {
            initialMapping[s.targetField] = s.csvColumn;
          });
          setMapping(initialMapping);
          setStep('mapping');
        } else {
          alert("L'analyse du fichier a échoué. Vérifiez le format de votre fichier.");
        }
      } catch (err: any) {
        console.error("Analysis failed", err);
        alert("Erreur lors de l'analyse : " + (err.message || "Serveur injoignable"));
      }
    };

    if (isExcel) {
      reader.readAsDataURL(file); // Envoie en Base64 pour Excel
    } else {
      reader.readAsText(file); // Texte pour CSV
    }
  };

  const handleImport = async () => {
    try {
      const { data } = await smartImport({
        variables: {
          input: {
            storeId: selectedStoreId,
            csvContent,
            mapping: JSON.stringify(mapping)
          }
        }
      });
      if (data.smartImport.success) {
        setImportResult(data.smartImport);
        setStep('success');
      } else {
        alert("Erreur lors de l'importation : " + data.smartImport.message);
      }
    } catch (err: any) {
      console.error("Import failed", err);
      alert("Une erreur technique est survenue : " + err.message);
    }
  };

  // --- Renderers ---

  return (
    <PermissionGuard permission={Permission.INVENTORY_IMPORT}>
    <div className="max-w-5xl mx-auto py-4 px-4 space-y-4 animate-in fade-in duration-500 relative">
      
      {/* Loading Overlays */}
      {analyzing && <LoadingOverlay message="Analyse intelligente en cours..." />}
      {importing && <LoadingOverlay message="Finalisation de l'importation..." />}
      
      {/* Header Compact */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/5 rounded-xl">
            <Sparkles className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 tracking-tight">{t('title')}</h1>
            <p className="text-xs text-slate-500 font-medium">{t('subtitle')}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {['upload', 'mapping', 'preview', 'success'].map((s, i) => (
            <React.Fragment key={s}>
              <div className={cn(
                "h-1.5 w-8 rounded-full transition-all duration-500",
                step === s ? "bg-primary w-12" : "bg-slate-100"
              )} />
            </React.Fragment>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        {step === 'upload' && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4"
          >
            <div className="p-4 bg-white border border-slate-100 rounded-2xl flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary/5 rounded-lg flex items-center justify-center">
                  <Database className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{t('destination.label')}</p>
                  <p className="text-xs font-bold text-slate-900">{t('destination.choose')}</p>
                </div>
              </div>
              
              <CustomSelect 
                options={storeOptions}
                value={selectedStoreId}
                onChange={setSelectedStoreId}
                placeholder={t('destination.choose')}
              />
            </div>

            <div 
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-200 rounded-3xl p-6 sm:p-12 flex flex-col items-center justify-center bg-white hover:bg-slate-50/50 hover:border-primary/30 transition-all cursor-pointer group"
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept=".csv" 
                onChange={handleFileUpload} 
              />
              <div className="w-14 h-14 bg-primary/5 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Upload className="h-7 w-7 text-primary" />
              </div>
              <h2 className="text-base font-bold text-slate-900 mb-1">{t('dropzone.title')}</h2>
              <p className="text-xs text-slate-400 font-medium max-w-[280px] text-center leading-relaxed">
                {t('dropzone.subtitle')}
              </p>
              
              <div className="mt-6 px-5 py-2 bg-slate-900 text-white rounded-xl text-[11px] font-bold shadow-lg shadow-slate-200 hover:scale-105 transition-transform">
                {t('dropzone.button')}
              </div>
            </div>
          </motion.div>
        )}

        {/* STEP 2: SMART MAPPING */}
        {step === 'mapping' && analysis && (
          <motion.div
            key="mapping"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="grid grid-cols-1 lg:grid-cols-[1fr_350px] gap-8"
          >
            <div className="space-y-6">
              {/* Impact Summary Alert */}
              {analysis.impactSummary && (
                <div className="p-4 bg-blue-50 border border-blue-100 rounded-2xl flex items-start gap-3 animate-in fade-in duration-500">
                  <div className="p-2 bg-blue-100 rounded-lg shrink-0">
                    <Database className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-blue-900">Résumé de l'analyse IA</h4>
                    <p className="text-[11px] text-blue-700 font-medium leading-relaxed">
                      {analysis.impactSummary}
                    </p>
                  </div>
                </div>
              )}

              <div className="bg-white rounded-3xl border border-slate-100 p-8 space-y-8">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-amber-500" />
                    Mapping des colonnes
                  </h2>
                  <span className="text-xs font-bold bg-amber-50 text-amber-600 px-3 py-1 rounded-full border border-amber-100">
                    Suggéré par l'IA
                  </span>
                </div>

                <div className="space-y-4">
                  {Object.entries(mapping).map(([target, currentVal]) => {
                    const suggestion = analysis.suggestedMapping.find((s: any) => s.targetField === target);
                    const isAISuggested = suggestion?.csvColumn === currentVal;
                    const confidence = suggestion?.confidence || 0;
                    
                    return (
                      <div key={target} className="flex items-center gap-4 group">
                        <div className="w-40 flex flex-col">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{target}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-slate-700 capitalize">{target.replace('_', ' ')}</span>
                            {isAISuggested && (
                              <div 
                                className={cn(
                                  "w-1.5 h-1.5 rounded-full",
                                  confidence > 0.8 ? "bg-emerald-500" : confidence > 0.5 ? "bg-amber-500" : "bg-red-500"
                                )} 
                                title={`Confiance IA: ${Math.round(confidence * 100)}%`}
                              />
                            )}
                          </div>
                        </div>
                        
                        <div className="flex-1 flex items-center gap-3">
                          <div className="h-[1px] flex-1 bg-slate-100" />
                          <div className="w-[250px]">
                            <CustomSelect
                              options={analysis.columns.map((col: string) => ({ value: col, label: col }))}
                              value={currentVal}
                              onChange={(val) => setMapping({...mapping, [target]: val})}
                              placeholder="Sélectionner..."
                              className={cn(
                                "border rounded-2xl",
                                isAISuggested ? "border-slate-100 bg-slate-50" : "border-amber-200 bg-amber-50/30"
                              )}
                            />
                            {!isAISuggested && currentVal && (
                              <button 
                                onClick={() => setMapping({...mapping, [target]: suggestion?.csvColumn || ''})}
                                className="mt-1 ml-2 text-[10px] font-bold text-amber-600 hover:underline shrink-0"
                              >
                                Rétablir IA
                              </button>
                            )}
                          </div>
                          <div className="h-[1px] flex-1 bg-slate-100" />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="pt-6 flex justify-between">
                  <button 
                    onClick={() => setStep('upload')}
                    className="px-6 py-2.5 text-sm font-bold text-slate-500 hover:text-slate-900 transition-colors flex items-center gap-2"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Retour
                  </button>
                  <button 
                    onClick={() => setStep('preview')}
                    className="px-8 py-2.5 bg-primary text-white rounded-xl text-sm font-bold shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                  >
                    Vérifier les données
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Sidebar info */}
            <div className="space-y-6">
              <div className="bg-slate-900 rounded-3xl p-6 text-white space-y-4">
                <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                  <Search className="h-5 w-5 text-white" />
                </div>
                <h3 className="font-bold">Aide au Mapping</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  L'IA a identifié <span className="text-white font-bold">{analysis.suggestedMapping.length} colonnes</span> avec certitude. Vérifiez le mapping avant de passer à l'étape suivante.
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* STEP 3: PREVIEW */}
        {step === 'preview' && analysis && (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-6"
          >
            <div className="bg-white rounded-3xl border border-slate-100 overflow-hidden">
              <div className="p-8 border-b border-slate-50 flex items-center justify-between bg-slate-50/30">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Aperçu final</h2>
                  <p className="text-sm text-slate-500">Vérifiez les premières lignes avant l'injection.</p>
                </div>
                <div className="flex items-center gap-3">
                   <button 
                    onClick={() => setStep('mapping')}
                    className="h-10 px-4 text-sm font-bold text-slate-500 hover:text-slate-900 transition-all"
                  >
                    Ajuster le mapping
                  </button>
                  <button 
                    onClick={handleImport}
                    disabled={importing}
                    className="h-10 px-6 bg-slate-900 text-white rounded-xl text-sm font-bold shadow-xl shadow-slate-900/10 hover:bg-slate-800 transition-all flex items-center gap-2"
                  >
                    {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                    Lancer l'importation
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/50">
                      {Object.keys(mapping).map((key) => (
                        <th key={key} className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {(() => {
                      try {
                        const data = typeof analysis.sampleData === 'string' ? JSON.parse(analysis.sampleData) : analysis.sampleData;
                        const anoms = typeof analysis.anomalies === 'string' ? JSON.parse(analysis.anomalies) : (analysis.anomalies || []);
                        
                        return data.map((row: any, i: number) => {
                          const rowAnomalies = anoms.find((a: any) => a.row === i);
                          
                          return (
                            <tr key={i} className="hover:bg-slate-50/30 transition-colors">
                              {Object.entries(mapping).map(([target, csvCol]) => {
                                const error = rowAnomalies?.errors[csvCol as string];
                                const cellValue = row[csvCol as string];
                                
                                return (
                                  <td key={target} className="px-6 py-4 text-sm font-medium">
                                    <div className="flex items-center gap-2">
                                      <span className={cn(
                                        "text-slate-700",
                                        error ? "text-red-600 font-bold" : ""
                                      )}>
                                        {cellValue || '-'}
                                      </span>
                                      {error && (
                                        <div className="group relative">
                                          <AlertCircle className="h-3.5 w-3.5 text-red-500 cursor-help" />
                                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-white text-[10px] rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                                            {error === 'NEGATIVE_VALUE' ? 'Valeur négative' : 'Donnée manquante'}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                          );
                        });
                      } catch (e) {
                        return <tr><td colSpan={100} className="p-4 text-center text-red-500 text-xs font-bold">Erreur de lecture des données.</td></tr>;
                      }
                    })()}
                  </tbody>
                </table>
              </div>
            </div>
          </motion.div>
        )}

        {/* STEP 4: SUCCESS */}
        {step === 'success' && (
          <motion.div
            key="success"
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-[2rem] p-8 border border-slate-100 flex flex-col items-center text-center shadow-lg shadow-slate-200/40"
          >
            <div className="relative mb-5">
              <div className="absolute inset-0 bg-emerald-400/10 rounded-full blur-xl animate-pulse" />
              <div className="relative w-16 h-16 bg-emerald-500 text-white rounded-full flex items-center justify-center shadow-lg shadow-emerald-100">
                <CheckCircle2 className="h-8 w-8" />
              </div>
            </div>

            <div className="space-y-1 mb-6">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Importation terminée</h2>
              <p className="text-xs text-slate-500 max-w-[280px] mx-auto font-medium">
                Michi IA a synchronisé vos données. Votre inventaire est maintenant à jour.
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-3 w-full max-w-[320px] mb-8">
              <div className="bg-slate-50/50 rounded-2xl p-4 border border-slate-100 flex flex-col items-center group transition-colors duration-300">
                <div className="w-8 h-8 bg-blue-50 text-blue-500 rounded-lg flex items-center justify-center mb-2">
                  <Package className="h-4 w-4" />
                </div>
                <p className="text-[9px] font-bold text-slate-400 tracking-widest mb-0.5">Produits</p>
                <p className="text-xl font-black text-slate-900">{importResult?.productsCount || 0}</p>
              </div>
              <div className="bg-slate-50/50 rounded-2xl p-4 border border-slate-100 flex flex-col items-center group transition-colors duration-300">
                <div className="w-8 h-8 bg-amber-50 text-amber-500 rounded-lg flex items-center justify-center mb-2">
                  <TrendingUp className="h-4 w-4" />
                </div>
                <p className="text-[9px] font-bold text-slate-400 tracking-widest mb-0.5">Historique</p>
                <p className="text-xl font-black text-slate-900">{importResult?.salesLogsCount || 0}</p>
              </div>
            </div>

            <div className="flex flex-col w-full max-w-[320px] gap-2">
              <button 
                onClick={() => router.push('/dashboard?tab=inventory')}
                className="w-full py-3 bg-slate-900 text-white rounded-xl font-bold shadow-lg shadow-slate-900/10 hover:bg-slate-800 active:scale-[0.98] transition-all flex items-center justify-center gap-2 text-sm"
              >
                Accéder à l'inventaire
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
              <button 
                onClick={() => setStep('upload')}
                className="w-full py-2 text-[11px] font-bold text-slate-400 hover:text-slate-900 transition-colors"
              >
                Importer un autre fichier
              </button>
            </div>
          </motion.div>
        )}

      </AnimatePresence>
    </div>
    </PermissionGuard>
  );
}
