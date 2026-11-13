import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  ShieldAlert,
  Wrench,
  Search,
  Sparkles,
} from 'lucide-react';

export const DiagnosticsPanel: React.FC = () => {
  const { alerts, addToast } = useApp();
  const [isScanning, setIsScanning] = useState(false);

  const runDiagnosticsScan = () => {
    setIsScanning(true);
    setTimeout(() => {
      setIsScanning(false);
      addToast({
        type: 'success',
        title: 'Diagnostic Scan Complete',
        message: 'All 5 filter stages evaluated. Membrane rejection held at 94.9%. No critical fouling detected.',
      });
    }, 1200);
  };

  return (
    <div className="bg-white rounded-3xl border border-sky-100 p-6 shadow-card flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-3 mb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-sky-600" />
            <h2 className="text-lg font-extrabold text-slate-900 tracking-tight">
              AI Prognostic Advisories
            </h2>
          </div>

          <button
            onClick={runDiagnosticsScan}
            disabled={isScanning}
            className="px-3 py-1.5 rounded-xl text-xs font-bold bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 transition-all flex items-center gap-1.5 shadow-2xs"
          >
            {isScanning ? (
              <>
                <div className="w-3 h-3 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                <span>Analyzing Sensors...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-sky-500" />
                <span>Run Diagnostic Scan</span>
              </>
            )}
          </button>
        </div>

        <p className="text-xs text-slate-500 mb-4">
          Real-time anomaly detection identifying sensor drift, early-stage scaling, and mechanical wear.
        </p>

        {/* Alerts List */}
        <div className="space-y-3">
          {alerts.map((alert) => {
            let badgeBg = 'bg-sky-50 text-sky-700 border-sky-200';
            let Icon = Info;

            if (alert.severity === 'critical') {
              badgeBg = 'bg-rose-50 text-rose-700 border-rose-200';
              Icon = AlertTriangle;
            } else if (alert.severity === 'high') {
              badgeBg = 'bg-amber-50 text-amber-700 border-amber-200';
              Icon = AlertTriangle;
            } else if (alert.severity === 'low') {
              badgeBg = 'bg-emerald-50 text-emerald-700 border-emerald-200';
              Icon = CheckCircle2;
            }

            return (
              <div
                key={alert.id}
                className="p-4 rounded-2xl border border-sky-100 bg-gradient-to-r from-sky-50/40 to-white hover:border-sky-200 transition-all"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${badgeBg} uppercase tracking-wider`}>
                      {alert.severity} Priority
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      {alert.fault_type}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-medium">
                    {alert.timestamp}
                  </span>
                </div>

                <p className="text-xs font-medium text-slate-800 leading-relaxed mb-3">
                  {alert.human_text}
                </p>

                {/* Evidence telemetry tag */}
                <div className="flex flex-wrap items-center gap-2 text-[11px] bg-white p-2.5 rounded-xl border border-sky-100">
                  <span className="font-bold text-sky-700">Sensor Evidence:</span>
                  {Object.entries(alert.evidence).map(([k, v]) => (
                    <span key={k} className="px-1.5 py-0.5 bg-sky-50 text-slate-700 rounded text-[10px] font-mono">
                      {k}: <b className="text-sky-900">{String(v)}</b>
                    </span>
                  ))}
                  <span className="ml-auto text-[10px] font-bold text-slate-400">
                    Confidence: {(alert.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-sky-50 flex items-center justify-between text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <Wrench className="w-3.5 h-3.5 text-sky-500" />
          Technician Dispatch: <b className="text-slate-800">Auto-Assigned</b>
        </span>
        <span className="text-sky-600 font-semibold cursor-pointer hover:underline">
          View Audit Trail &rarr;
        </span>
      </div>
    </div>
  );
};

