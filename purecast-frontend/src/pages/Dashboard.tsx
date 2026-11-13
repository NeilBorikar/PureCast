import React from 'react';
import { useApp } from '../context/AppContext';
import { FilterCard } from '../components/FilterCard';
import { TelemetryStream } from '../components/TelemetryStream';
import { WearChart } from '../components/WearChart';
import { DiagnosticsPanel } from '../components/DiagnosticsPanel';
import {
  ShieldCheck,
  Droplets,
  Calendar,
  Layers,
  ArrowUpRight,
  MapPin,
  Clock,
  Sparkles,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { selectedDevice, user, tenant } = useApp();

  return (
    <div className="space-y-6 pb-12">
      {/* Hero Banner: Device Details & Quick Summary */}
      <div className="bg-gradient-to-r from-sky-500 via-sky-600 to-sky-700 rounded-3xl p-6 sm:p-8 text-white shadow-card relative overflow-hidden">
        {/* Decorative waves & bubbles */}
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-white/10 rounded-full blur-2xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 bg-sky-400/20 rounded-full blur-xl pointer-events-none" />

        <div className="relative z-10 flex flex-wrap items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md text-sky-100 text-xs font-semibold mb-3 border border-white/20">
              <Sparkles className="w-3.5 h-3.5 text-sky-200" />
              <span>Multi-Tenant Advisory Engine • {tenant.name}</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white leading-tight">
              {selectedDevice.model_name}
            </h1>

            <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs text-sky-100 mt-2">
              <span className="flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse" />
                Serial: <b className="text-white font-mono">{selectedDevice.serial_number}</b>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 font-medium">
                <MapPin className="w-3.5 h-3.5 text-sky-200" />
                {selectedDevice.household_name} ({selectedDevice.household_address})
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 font-medium">
                <Clock className="w-3.5 h-3.5 text-sky-200" />
                Tier: <b className="text-white">{selectedDevice.device_tier}</b>
              </span>
            </div>
          </div>

          {/* Quick Action Badge */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4 text-center min-w-[150px]">
            <span className="text-[11px] font-bold text-sky-100 uppercase tracking-wider block">
              System Health
            </span>
            <div className="text-3xl font-black text-white mt-0.5">92.4%</div>
            <span className="text-[11px] text-emerald-300 font-semibold flex items-center justify-center gap-1 mt-1">
              <ShieldCheck className="w-3.5 h-3.5" /> All Stages Safe
            </span>
          </div>
        </div>
      </div>

      {/* 5-Filter Health Prognostic Cards */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
              <Layers className="w-5 h-5 text-sky-600" />
              Cartridge Health & Prognostic Forecasts
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live Remaining Useful Life (RUL) with sensor-derived wear rates
            </p>
          </div>
          <span className="text-xs font-bold text-sky-700 bg-sky-50 border border-sky-200 px-3 py-1 rounded-xl">
            {selectedDevice.cartridges.length} Cartridge Stages
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {selectedDevice.cartridges.map((cartridge) => (
            <FilterCard key={cartridge.id} cartridge={cartridge} />
          ))}
        </div>
      </div>

      {/* Live Hydro-Flow Telemetry Stream */}
      <TelemetryStream />

      {/* Analytics & AI Diagnostics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <WearChart />
        </div>
        <div className="lg:col-span-5">
          <DiagnosticsPanel />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
