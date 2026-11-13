import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { useApp } from '../context/AppContext';
import { TrendingDown, Waves, Calendar, Filter } from 'lucide-react';

export const WearChart: React.FC = () => {
  const { selectedDevice } = useApp();
  const [activeTab, setActiveTab] = useState<'wear' | 'tds'>('wear');

  // Generate 12-month prognostic wear curve data
  const wearData = [
    { month: 'Month 0', sediment: 100, carbon: 100, ro: 100, uv: 100, bandHigh: 100, bandLow: 100 },
    { month: 'Month 1', sediment: 91, carbon: 95, ro: 99, uv: 98, bandHigh: 94, bandLow: 88 },
    { month: 'Month 2', sediment: 82, carbon: 90, ro: 97, uv: 95, bandHigh: 86, bandLow: 78 },
    { month: 'Month 3', sediment: 74, carbon: 85, ro: 96, uv: 92, bandHigh: 79, bandLow: 69 },
    { month: 'Month 4 (Now)', sediment: 64, carbon: 82, ro: 94, uv: 86, bandHigh: 70, bandLow: 58 },
    { month: 'Month 5 (Proj)', sediment: 52, carbon: 76, ro: 91, uv: 82, bandHigh: 60, bandLow: 44 },
    { month: 'Month 6 (Proj)', sediment: 38, carbon: 70, ro: 88, uv: 78, bandHigh: 48, bandLow: 28 },
    { month: 'Month 7 (Proj)', sediment: 24, carbon: 64, ro: 85, uv: 72, bandHigh: 34, bandLow: 14 },
    { month: 'Month 8 (Proj)', sediment: 12, carbon: 58, ro: 82, uv: 68, bandHigh: 22, bandLow: 5 },
    { month: 'Month 9 (Proj)', sediment: 0, carbon: 52, ro: 79, uv: 62, bandHigh: 10, bandLow: 0 },
  ];

  // Daily TDS rejection and volume filtered
  const tdsData = [
    { day: 'Mon', tdsIn: 720, tdsOut: 36, liters: 15.2 },
    { day: 'Tue', tdsIn: 745, tdsOut: 38, liters: 18.5 },
    { day: 'Wed', tdsIn: 730, tdsOut: 35, liters: 14.8 },
    { day: 'Thu', tdsIn: 780, tdsOut: 42, liters: 19.1 },
    { day: 'Fri', tdsIn: 755, tdsOut: 39, liters: 16.4 },
    { day: 'Sat', tdsIn: 710, tdsOut: 34, liters: 22.0 },
    { day: 'Sun', tdsIn: 735, tdsOut: 37, liters: 24.5 },
  ];

  return (
    <div className="bg-white rounded-3xl border border-sky-100 p-6 shadow-card">
      {/* Header and View Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <TrendingDown className="w-5 h-5 text-sky-500" />
            <h2 className="text-lg font-extrabold text-slate-900 tracking-tight">
              Predictive Wear Trajectory & Diagnostics
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Machine Learning RUL prognosis based on sensor drift and water volume
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center p-1 bg-sky-50 rounded-xl border border-sky-100">
          <button
            onClick={() => setActiveTab('wear')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'wear'
                ? 'bg-white text-sky-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Filter Health Curves
          </button>
          <button
            onClick={() => setActiveTab('tds')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'tds'
                ? 'bg-white text-sky-700 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            TDS Rejection History
          </button>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-72 w-full">
        {activeTab === 'wear' ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={wearData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="sedimentGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0284c7" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="bandGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#bae6fd" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#bae6fd" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f9ff" vertical={false} />
              <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} tickLine={false} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '16px',
                  border: '1px solid #e0f2fe',
                  boxShadow: '0 10px 25px -5px rgba(2, 132, 199, 0.1)',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <ReferenceLine y={20} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: 'Replace (20%)', fill: '#f43f5e', fontSize: 10, position: 'insideBottomRight' }} />
              
              {/* Confidence Band for Sediment */}
              <Area
                type="monotone"
                dataKey="bandHigh"
                stroke="none"
                fill="url(#bandGrad)"
                name="Confidence Range"
              />
              <Area
                type="monotone"
                dataKey="sediment"
                stroke="#0284c7"
                strokeWidth={2.5}
                fill="url(#sedimentGrad)"
                name="Sediment Filter"
              />
              <Line
                type="monotone"
                dataKey="carbon"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
                name="Carbon Block"
              />
              <Line
                type="monotone"
                dataKey="ro"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                name="RO Membrane"
              />
              <Line
                type="monotone"
                dataKey="uv"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={false}
                name="UV Lamp"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={tdsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f9ff" vertical={false} />
              <XAxis dataKey="day" stroke="#94a3b8" fontSize={11} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '16px',
                  border: '1px solid #e0f2fe',
                  boxShadow: '0 10px 25px -5px rgba(2, 132, 199, 0.1)',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Line
                type="monotone"
                dataKey="tdsIn"
                stroke="#64748b"
                strokeWidth={2}
                strokeDasharray="4 4"
                name="Raw Municipal TDS (ppm)"
              />
              <Line
                type="monotone"
                dataKey="tdsOut"
                stroke="#0284c7"
                strokeWidth={3}
                name="Purified Water TDS (ppm)"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

