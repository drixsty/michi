import React from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell 
} from 'recharts';
import { Database } from 'lucide-react';

interface ChartProps {
  config: {
    type: 'bar' | 'line' | 'pie';
    title?: string;
    data: any[];
  }
}

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

export const AssistantChart: React.FC<ChartProps> = ({ config }) => {
  const { type, title, data } = config;

  return (
    <div className="my-6 p-5 bg-white border border-slate-100 rounded-2xl shadow-sm overflow-hidden">
      <div className="text-[11px] font-bold text-slate-400 tracking-wider mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-indigo-50 rounded-md flex items-center justify-center text-indigo-500">
                <Database size={12} />
            </div>
            <span className="uppercase">{title || "Analyse de données"}</span>
        </div>
        <div className="flex gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
            <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
        </div>
      </div>
      
      <div className="h-[240px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          {type === 'bar' ? (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f8fafc" />
              <XAxis 
                dataKey="name" 
                fontSize={10} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#94a3b8' }}
                dy={10}
              />
              <YAxis 
                fontSize={10} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#94a3b8' }}
              />
              <Tooltip 
                cursor={{ fill: '#f1f5f9' }}
                contentStyle={{ 
                    borderRadius: '12px', 
                    border: 'none', 
                    boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)',
                    fontSize: '12px',
                    fontWeight: 'bold'
                }}
              />
              <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} barSize={32} />
            </BarChart>
          ) : type === 'line' ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f8fafc" />
              <XAxis 
                dataKey="name" 
                fontSize={10} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#94a3b8' }}
                dy={10}
              />
              <YAxis 
                fontSize={10} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fill: '#94a3b8' }}
              />
              <Tooltip 
                contentStyle={{ 
                    borderRadius: '12px', 
                    border: 'none', 
                    boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
                    fontSize: '12px'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#4f46e5" 
                strokeWidth={3} 
                dot={{ fill: '#4f46e5', strokeWidth: 2, r: 4, stroke: '#fff' }}
                activeDot={{ r: 6, strokeWidth: 0 }}
              />
            </LineChart>
          ) : (
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                 contentStyle={{ 
                    borderRadius: '12px', 
                    border: 'none', 
                    boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)',
                    fontSize: '12px'
                }}
              />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};
