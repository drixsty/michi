'use client';

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { CleanedDemand } from '@michi/types';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

interface SalesChartProps {
  data: CleanedDemand[];
  title?: string;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const d = payload[0].payload as CleanedDemand;
    return (
      <div className="bg-white p-3 border border-gray-100 shadow-xl rounded-xl text-xs">
        <p className="font-bold text-gray-900 mb-1">
          {format(new Date(label), 'd MMMM yyyy', { locale: fr })}
        </p>
        <div className="space-y-1">
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Ventes Corrigées:</span>
            <span className="font-mono font-bold text-purple-600">{(d.correctedUnitsSold ?? 0).toFixed(2)} u.</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Ventes Brutes:</span>
            <span className="font-mono text-gray-500">{(d.rawUnitsSold ?? 0).toFixed(2)} u.</span>
          </div>
          {d.correctionType !== 'none' && (
            <div className="mt-2 pt-2 border-t border-gray-50 flex items-center gap-1.5 text-amber-600 font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
              <span>
                {d.correctionType === 'stockout' ? 'Rupture corrigée' : 
                 d.correctionType === 'outlier' ? 'Anomalie filtrée' : 
                 'Correction IA'}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export default function SalesChart({ data, title }: SalesChartProps) {
  // On ne garde que les 90 derniers jours pour la lisibilité
  const displayData = data.slice(0, 90).reverse();

  return (
    <div className="w-full h-full min-h-[300px] flex flex-col">
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
          <div className="flex items-center gap-4 text-[10px] font-medium uppercase tracking-wider">
            <div className="flex items-center gap-1.5">
              <div className="h-2 w-2 rounded-full bg-purple-500" />
              <span className="text-gray-500">Nettoyé</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-0.5 w-3 bg-gray-300" />
              <span className="text-gray-400">Brut</span>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={displayData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorCleaned" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#9333ea" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#9333ea" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
            <XAxis 
              dataKey="date" 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: '#9ca3af' }}
              tickFormatter={(str) => format(new Date(str), 'MMM', { locale: fr })}
              interval={15}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: '#9ca3af' }}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* Ventes Brutes (Fond) */}
            <Area
              type="monotone"
              dataKey="rawUnitsSold"
              stroke="#e5e7eb"
              strokeWidth={1}
              strokeDasharray="4 4"
              fill="transparent"
              dot={false}
              activeDot={false}
            />
            
            {/* Ventes Nettoyées (Premier plan) */}
            <Area
              type="monotone"
              dataKey="correctedUnitsSold"
              stroke="#9333ea"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorCleaned)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0, fill: '#9333ea' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
