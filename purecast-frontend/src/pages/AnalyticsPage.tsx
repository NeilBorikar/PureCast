import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  RadialBarChart,
  RadialBar,
} from 'recharts';
import { useApp } from '../context/AppContext';
import {
  LineChart as ChartIcon,
  Sparkles,
  TrendingUp,
  Droplet,
  ShieldCheck,
  Award,
  Layers,
  Clock,
} from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const { tenant } = useApp();

  const volumeData = [
    { month: 'Jan', liters: 12400, savings: 320 },
    { month: 'Feb', liters: 14200, savings: 380 },
    { month: 'Mar', liters: 16800, savings: 450 },
    { month: 'Apr', liters: 15300, savings: 410 },
    { month: 'May', liters: 18900, savings: 520 },
    { month: 'Jun', liters: 21400, savings: 590 },
    { month: 'Jul', liters: 24200, savings: 660 },
  ];

  const stageWearComparison = [
    { stage: 'Sediment', avgLifeDays: 95, ratedDays: 120, wearFactor: '1.26x (Turbidity)' },
    { stage: 'Carbon Block', avgLifeDays: 180, ratedDays: 180, wearFactor: '1.00x (Chlorine)' },
    { stage: 'Membrane Shield', avgLifeDays: 240, ratedDays: 240, wearFactor: '1.00x (Hardness)' },
    { stage: 'RO Membrane', avgLifeDays: 480, ratedDays: 365, wearFactor: '0.76x (Optimal Flux)' },
    { stage: 'UV Sterilizer', avgLifeDays: 350, ratedDays: 365, wearFactor: '0.96x (Current)' },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          <ChartIcon className="w-6 h-6 text-sky-600" />
          Prognostic Intelligence & Analytics
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Machine learning telemetry analysis, consumable wear curves, and filtration ROI for{' '}
          <span className="font-semibold text-slate-700">{tenant.name}</span>
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-3xl border border-sky-100 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Purified Water</span>
            <Droplet className="w-4 h-4 text-sky-500" />
          </div>
          <div className="text-2xl font-black text-slate-900 tracking-tight">123,200 L</div>
          <span className="text-[11px] font-semibold text-emerald-600 flex items-center gap-1 mt-1">
            <TrendingUp className="w-3.5 h-3.5" /> +14.2% vs last month
          </span>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-sky-100 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Average RO Rejection</span>
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-black text-emerald-700 tracking-tight">95.2%</div>
          <span className="text-[11px] font-semibold text-slate-500 mt-1 block">
            Over 720 ppm municipal TDS
          </span>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-sky-100 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Filter Life Extended</span>
            <Sparkles className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-sky-900 tracking-tight">+38 Days</div>
          <span className="text-[11px] font-semibold text-sky-700 mt-1 block">
            Via Dynamic RUL vs Calendar
          </span>
        </div>

        <div className="bg-white p-5 rounded-3xl border border-sky-100 shadow-card">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Prognostic Precision</span>
            <Award className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-2xl font-black text-slate-900 tracking-tight">98.4%</div>
          <span className="text-[11px] font-semibold text-emerald-600 mt-1 block">
            ±4.2 days RUL error margin
          </span>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Treated Water & Savings Bar Chart */}
        <div className="lg:col-span-8 bg-white p-6 rounded-3xl border border-sky-100 shadow-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-base font-extrabold text-slate-900 tracking-tight">
                Monthly Water Volume Treated (Liters)
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Total hydro-consumption across all active tenant purifier units
              </p>
            </div>
            <span className="text-xs font-bold px-3 py-1 rounded-xl bg-sky-50 text-sky-700 border border-sky-100">
              YTD 2026
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={volumeData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f9ff" vertical={false} />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
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
                <Bar dataKey="liters" fill="#0ea5e9" radius={[8, 8, 0, 0]} name="Purified Liters" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Consumable Lifespan Benchmark Card */}
        <div className="lg:col-span-4 bg-white p-6 rounded-3xl border border-sky-100 shadow-card flex flex-col justify-between">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 tracking-tight mb-1">
              Filter Degradation Breakdown
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Real telemetry wear compared against factory-rated baseline.
            </p>

            <div className="space-y-3.5">
              {stageWearComparison.map((stg) => (
                <div key={stg.stage} className="p-3 rounded-2xl bg-sky-50/50 border border-sky-100">
                  <div className="flex justify-between items-center text-xs mb-1">
                    <span className="font-bold text-slate-800">{stg.stage}</span>
                    <span className="text-[11px] font-mono text-sky-700 font-bold">
                      {stg.avgLifeDays} / {stg.ratedDays} d
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-sky-200/50 rounded-full overflow-hidden mb-1.5">
                    <div
                      className="h-full bg-sky-500 rounded-full"
                      style={{ width: `${Math.min(100, (stg.avgLifeDays / stg.ratedDays) * 100)}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Primary Driver: <b className="text-slate-700">{stg.wearFactor}</b>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-sky-50 mt-4 text-[11px] text-slate-500">
            Powered by PureCast Physics-Informed ML Kernel
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;

