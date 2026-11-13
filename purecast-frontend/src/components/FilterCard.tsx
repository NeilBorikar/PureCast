import React, { useState } from 'react';
import { FilterCartridge, ConsumableType } from '../types';
import { useApp } from '../context/AppContext';
import {
  ShieldCheck,
  Sparkles,
  Zap,
  Filter,
  Layers,
  Calendar,
  Gauge,
  Truck,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

interface FilterCardProps {
  cartridge: FilterCartridge;
}

const CARTRIDGE_INFO: Record<
  ConsumableType,
  { label: string; stage: string; desc: string; icon: React.ComponentType<{ className?: string }> }
> = {
  SEDIMENT: {
    label: 'Sediment Pre-Filter',
    stage: 'Stage 1 — Mechanical',
    desc: 'Traps sand, rust, silt, and coarse suspended solids down to 5 microns.',
    icon: Filter,
  },
  CARBON: {
    label: 'Activated Carbon Block',
    stage: 'Stage 2 — Adsorption',
    desc: 'Removes chlorine taste, pesticides, and volatile organic compounds (VOCs).',
    icon: Layers,
  },
  MEMBRANE_PROTECTOR: {
    label: 'Membrane Protector',
    stage: 'Stage 3 — Anti-Scalant',
    desc: 'Chelates calcium and magnesium ions to inhibit RO membrane scaling.',
    icon: ShieldCheck,
  },
  RO_MEMBRANE: {
    label: 'Thin-Film RO Membrane',
    stage: 'Stage 4 — Hyperfiltration',
    desc: 'Separates dissolved salts, heavy metals, arsenic, and micro-plastics (0.0001 µm).',
    icon: Gauge,
  },
  UV_LAMP: {
    label: 'UV-C Sterilization Lamp',
    stage: 'Stage 5 — Germicidal',
    desc: 'Destroys viral and bacterial DNA with 254nm ultraviolet radiation.',
    icon: Zap,
  },
};

export const FilterCard: React.FC<FilterCardProps> = ({ cartridge }) => {
  const { reorderCartridge } = useApp();
  const [isOrdering, setIsOrdering] = useState(false);
  const [justOrdered, setJustOrdered] = useState(false);

  const info = CARTRIDGE_INFO[cartridge.consumable_type] || {
    label: cartridge.consumable_type,
    stage: 'Cartridge Stage',
    desc: 'Purification filter element',
    icon: Filter,
  };

  const Icon = info.icon;

  // Circular gauge calculations
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    circumference - (cartridge.current_health_percentage / 100) * circumference;

  let gaugeColor = 'stroke-sky-500';
  let badgeClass = 'bg-sky-50 text-sky-700 border-sky-200';

  if (cartridge.current_health_percentage > 70) {
    gaugeColor = 'stroke-emerald-500';
    badgeClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (cartridge.current_health_percentage > 40) {
    gaugeColor = 'stroke-sky-500';
    badgeClass = 'bg-sky-50 text-sky-700 border-sky-200';
  } else if (cartridge.current_health_percentage > 20) {
    gaugeColor = 'stroke-amber-500';
    badgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
  } else {
    gaugeColor = 'stroke-rose-500';
    badgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
  }

  const handleReorder = () => {
    setIsOrdering(true);
    setTimeout(() => {
      reorderCartridge(cartridge);
      setIsOrdering(false);
      setJustOrdered(true);
      setTimeout(() => setJustOrdered(false), 5000);
    }, 600);
  };

  const percentUsed = Math.min(
    100,
    Math.round((cartridge.liters_filtered / cartridge.rated_capacity_liters) * 100)
  );

  return (
    <div className="bg-white rounded-2xl border border-sky-100 p-5 shadow-card hover:shadow-float hover:border-sky-300 transition-all flex flex-col justify-between group relative overflow-hidden">
      {/* Decorative gradient corner glow */}
      <div className="absolute top-0 right-0 w-28 h-28 bg-gradient-to-bl from-sky-100/50 via-sky-50/20 to-transparent rounded-bl-full pointer-events-none" />

      <div>
        {/* Top Header: Stage tag & Status */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-[11px] font-bold text-sky-600 uppercase tracking-wider bg-sky-50 px-2 py-0.5 rounded-md border border-sky-100">
            {info.stage}
          </span>
          <span
            className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${badgeClass} uppercase tracking-wide`}
          >
            {cartridge.status_text.replace('_', ' ')}
          </span>
        </div>

        {/* Title & Icon */}
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center flex-shrink-0 border border-sky-100 group-hover:bg-sky-500 group-hover:text-white transition-colors shadow-xs">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm leading-snug group-hover:text-sky-700 transition-colors">
              {info.label}
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
              SN: {cartridge.serial_number} | {cartridge.model_number}
            </p>
          </div>
        </div>

        {/* Middle Section: Circular Health Ring & Prognostic Days */}
        <div className="bg-gradient-to-b from-sky-50/50 to-white rounded-xl p-3.5 border border-sky-100/80 mb-4 flex items-center justify-around gap-2">
          {/* Radial Progress Ring */}
          <div className="relative w-24 h-24 flex items-center justify-center flex-shrink-0">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r={radius}
                className="stroke-sky-100"
                strokeWidth="7"
                fill="transparent"
              />
              <circle
                cx="50"
                cy="50"
                r={radius}
                className={`${gaugeColor} transition-all duration-1000 ease-out`}
                strokeWidth="7"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
              />
            </svg>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-lg font-extrabold text-slate-900 leading-none">
                {Math.round(cartridge.current_health_percentage)}%
              </span>
              <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold mt-0.5">
                Health
              </span>
            </div>
          </div>

          {/* RUL Remaining Forecast */}
          <div className="text-left">
            <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-500">
              <Calendar className="w-3.5 h-3.5 text-sky-500" />
              <span>Remaining Life:</span>
            </div>
            <div className="text-2xl font-black text-slate-900 tracking-tight mt-0.5">
              {cartridge.remaining_days}{' '}
              <span className="text-xs font-semibold text-slate-500">Days</span>
            </div>
            <div className="text-[11px] text-sky-700 bg-sky-100/60 px-2 py-0.5 rounded font-medium mt-1">
              Est: {cartridge.band_low} – {cartridge.band_high} d
            </div>
          </div>
        </div>

        {/* Liters Filtered Bar */}
        <div className="space-y-1.5 mb-4">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Water Treated</span>
            <span className="font-semibold text-slate-800">
              {cartridge.liters_filtered.toLocaleString()} / {cartridge.rated_capacity_liters.toLocaleString()} L ({percentUsed}%)
            </span>
          </div>
          <div className="w-full h-2 bg-sky-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-sky-400 to-sky-600 rounded-full transition-all duration-700"
              style={{ width: `${percentUsed}%` }}
            />
          </div>
        </div>

        <p className="text-xs text-slate-500 leading-relaxed line-clamp-2 mb-4">
          {info.desc}
        </p>
      </div>

      {/* Action Footer */}
      <div className="pt-2 border-t border-sky-50">
        <button
          onClick={handleReorder}
          disabled={isOrdering}
          className={`w-full py-2.5 px-3 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all shadow-sm ${
            justOrdered
              ? 'bg-emerald-500 text-white'
              : cartridge.remaining_days < 60
              ? 'bg-sky-600 hover:bg-sky-700 text-white shadow-sky-600/20'
              : 'bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200'
          }`}
        >
          {justOrdered ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-white" />
              <span>Dispatched to Technician!</span>
            </>
          ) : isOrdering ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
              <span>Ordering OEM Cartridge...</span>
            </>
          ) : (
            <>
              <Truck className="w-4 h-4" />
              <span>
                {cartridge.remaining_days < 60
                  ? 'Priority Reorder Cartridge'
                  : 'Order Replacement'}
              </span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

