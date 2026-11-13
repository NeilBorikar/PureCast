import React from 'react';
import { useApp } from '../context/AppContext';
import {
  Activity,
  Droplet,
  Gauge,
  Thermometer,
  Zap,
  Sparkles,
  Waves,
  ArrowRight,
  ShieldCheck,
  CheckCircle,
} from 'lucide-react';

export const TelemetryStream: React.FC = () => {
  const { telemetry, selectedDevice, togglePump } = useApp();

  const rejectionEfficiency = telemetry.tds_in > 0
    ? (((telemetry.tds_in - telemetry.tds_out) / telemetry.tds_in) * 100).toFixed(1)
    : '0';

  return (
    <div className="bg-white rounded-3xl border border-sky-100 p-6 shadow-card overflow-hidden relative">
      {/* Background Water Subtle Glow */}
      <div className="absolute -top-16 -right-16 w-64 h-64 bg-sky-100/60 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-16 -left-16 w-64 h-64 bg-sky-50 rounded-full blur-2xl pointer-events-none" />

      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 relative">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  telemetry.pump_running ? 'bg-sky-400' : 'bg-slate-300'
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                  telemetry.pump_running ? 'bg-sky-500' : 'bg-slate-400'
                }`}
              />
            </span>
            <h2 className="text-lg font-extrabold text-slate-900 tracking-tight">
              Live Sensor Telemetry & Hydro-Flow
            </h2>
            <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-sky-50 text-sky-700 border border-sky-200">
              IoT Telemetry v1
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time hydrodynamic sensor array for{' '}
            <span className="font-semibold text-slate-800">{selectedDevice.model_name}</span> ({selectedDevice.serial_number})
          </p>
        </div>

        {/* Live Status Tag */}
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-r from-sky-50 to-sky-100/60 border border-sky-200 rounded-2xl px-4 py-2 flex items-center gap-3">
            <div>
              <span className="text-[10px] text-sky-600 font-bold uppercase block">TDS Rejection</span>
              <span className="text-lg font-black text-sky-900 leading-none">{rejectionEfficiency}%</span>
            </div>
            <div className="w-8 h-8 rounded-xl bg-sky-500 text-white flex items-center justify-center shadow-xs">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>

          <button
            onClick={togglePump}
            className={`px-4 py-2.5 rounded-2xl text-xs font-bold transition-all flex items-center gap-2 shadow-sm ${
              telemetry.pump_running
                ? 'bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100'
                : 'bg-sky-600 text-white hover:bg-sky-700 shadow-sky-600/20'
            }`}
          >
            <Droplet className={`w-4 h-4 ${telemetry.pump_running ? 'animate-bounce' : ''}`} />
            <span>{telemetry.pump_running ? 'Stop Water Flow' : 'Dispense Water'}</span>
          </button>
        </div>
      </div>

      {/* Schematic Purifier Flow Diagram */}
      <div className="bg-gradient-to-b from-sky-50/70 via-white to-sky-50/40 rounded-2xl p-5 border border-sky-100 mb-6 relative overflow-hidden">
        <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
          <span>Municipal Water Inlet</span>
          <span className="text-sky-600 font-semibold flex items-center gap-1">
            <Waves className="w-3.5 h-3.5 text-sky-500 animate-pulse" /> Flow Active: {telemetry.flow_rate} L/min
          </span>
          <span className="text-emerald-600">Pure Permeate Faucet</span>
        </div>

        {/* 5-Stage Hydro Flow Pipe Pipeline */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 relative z-10">
          {/* Node 1: Inlet & P1 */}
          <div className="bg-white p-3.5 rounded-xl border border-sky-100 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-sky-600 uppercase">1. Raw Inlet</span>
              <Droplet className="w-4 h-4 text-sky-400" />
            </div>
            <div className="my-2">
              <div className="text-xl font-black text-slate-900">{telemetry.tds_in}</div>
              <div className="text-[10px] text-slate-400 font-medium">Inlet TDS (ppm)</div>
            </div>
            <div className="text-[11px] font-semibold text-slate-600 bg-sky-50/70 px-2 py-0.5 rounded">
              P1: {telemetry.pressure_p1} bar
            </div>
          </div>

          {/* Node 2: Sediment Filter */}
          <div className="bg-white p-3.5 rounded-xl border border-sky-100 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-sky-600 uppercase">2. Sediment</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <div className="my-2">
              <div className="text-xl font-black text-slate-900">{telemetry.turbidity}</div>
              <div className="text-[10px] text-slate-400 font-medium">Turbidity (NTU)</div>
            </div>
            <div className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
              Particulate Clear
            </div>
          </div>

          {/* Node 3: Carbon Block */}
          <div className="bg-white p-3.5 rounded-xl border border-sky-100 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-sky-600 uppercase">3. Carbon</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
            </div>
            <div className="my-2">
              <div className="text-xl font-black text-slate-900">0.02</div>
              <div className="text-[10px] text-slate-400 font-medium">Residual Cl (mg/L)</div>
            </div>
            <div className="text-[11px] font-semibold text-sky-700 bg-sky-50 px-2 py-0.5 rounded">
              VOC Absorption
            </div>
          </div>

          {/* Node 4: Booster Pump & P2 */}
          <div className={`p-3.5 rounded-xl border shadow-xs flex flex-col justify-between transition-colors ${
            telemetry.pump_running ? 'bg-sky-500 text-white border-sky-600' : 'bg-white text-slate-900 border-sky-100'
          }`}>
            <div className="flex items-center justify-between">
              <span className={`text-[10px] font-bold uppercase ${telemetry.pump_running ? 'text-sky-100' : 'text-sky-600'}`}>
                4. Pump
              </span>
              <Zap className={`w-4 h-4 ${telemetry.pump_running ? 'text-amber-300 animate-bounce' : 'text-slate-400'}`} />
            </div>
            <div className="my-2">
              <div className="text-xl font-black leading-none">{telemetry.pump_running ? 'ACTIVE' : 'IDLE'}</div>
              <div className={`text-[10px] mt-0.5 ${telemetry.pump_running ? 'text-sky-100' : 'text-slate-400'}`}>
                12V DC Booster
              </div>
            </div>
            <div className={`text-[11px] font-semibold px-2 py-0.5 rounded ${
              telemetry.pump_running ? 'bg-sky-600/70 text-white' : 'bg-slate-100 text-slate-600'
            }`}>
              P2: {telemetry.pressure_p2} bar
            </div>
          </div>

          {/* Node 5: RO Membrane */}
          <div className="bg-white p-3.5 rounded-xl border border-sky-100 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-sky-600 uppercase">5. RO Core</span>
              <Gauge className="w-4 h-4 text-sky-500" />
            </div>
            <div className="my-2">
              <div className="text-xl font-black text-emerald-600">{telemetry.tds_out}</div>
              <div className="text-[10px] text-slate-400 font-medium">Output TDS (ppm)</div>
            </div>
            <div className="text-[11px] font-semibold text-slate-600 bg-sky-50/70 px-2 py-0.5 rounded">
              P3: {telemetry.pressure_p3} bar
            </div>
          </div>

          {/* Node 6: UV Lamp & Permeate */}
          <div className="bg-white p-3.5 rounded-xl border border-sky-100 shadow-xs flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-sky-600 uppercase">6. UV-C Pure</span>
              <Sparkles className="w-4 h-4 text-amber-500" />
            </div>
            <div className="my-2">
              <div className="text-xl font-black text-slate-900">{telemetry.uv_current}</div>
              <div className="text-[10px] text-slate-400 font-medium">UV Ballast (mA)</div>
            </div>
            <div className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
              Zero Bacteria
            </div>
          </div>
        </div>
      </div>

      {/* Sensor Metrics Highlights Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-sky-50/50 rounded-2xl p-4 border border-sky-100 flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-white border border-sky-200 text-sky-600 flex items-center justify-center flex-shrink-0 shadow-xs">
            <Droplet className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-slate-500 font-medium block">Daily Water Dispensed</span>
            <div className="text-xl font-black text-slate-900 tracking-tight">
              {telemetry.today_liters.toFixed(1)}{' '}
              <span className="text-xs font-semibold text-slate-500">Liters</span>
            </div>
          </div>
        </div>

        <div className="bg-sky-50/50 rounded-2xl p-4 border border-sky-100 flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-white border border-sky-200 text-sky-600 flex items-center justify-center flex-shrink-0 shadow-xs">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-slate-500 font-medium block">Purification Flow</span>
            <div className="text-xl font-black text-slate-900 tracking-tight">
              {telemetry.flow_rate}{' '}
              <span className="text-xs font-semibold text-slate-500">L/min</span>
            </div>
          </div>
        </div>

        <div className="bg-sky-50/50 rounded-2xl p-4 border border-sky-100 flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-white border border-sky-200 text-sky-600 flex items-center justify-center flex-shrink-0 shadow-xs">
            <Thermometer className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-slate-500 font-medium block">Water Temperature</span>
            <div className="text-xl font-black text-slate-900 tracking-tight">
              {telemetry.temperature.toFixed(1)} <span className="text-xs font-semibold text-slate-500">°C</span>
            </div>
          </div>
        </div>

        <div className="bg-sky-50/50 rounded-2xl p-4 border border-sky-100 flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-xl bg-white border border-sky-200 text-emerald-600 flex items-center justify-center flex-shrink-0 shadow-xs">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-slate-500 font-medium block">WHO Safe Standard</span>
            <div className="text-xl font-black text-emerald-700 tracking-tight">
              Passed <span className="text-xs font-bold text-emerald-600">(100%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

