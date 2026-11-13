import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import {
  Droplets,
  Server,
  Activity,
  Zap,
  Play,
  Pause,
  RefreshCw,
  Building2,
  UserCheck,
  ChevronDown,
  Cpu,
  Layers,
  LineChart,
  Home,
  Check,
} from 'lucide-react';
import { DEMO_USERS, DEMO_TENANTS } from '../services/api';

export const Navbar: React.FC = () => {
  const {
    tenant,
    setTenant,
    user,
    setUser,
    selectedDevice,
    setSelectedDevice,
    devices,
    telemetry,
    togglePump,
    triggerTdsSpike,
    isSimulating,
    toggleSimulation,
    isBackendOnline,
    checkConnection,
  } = useApp();

  const [deviceDropdownOpen, setDeviceDropdownOpen] = useState(false);
  const [tenantDropdownOpen, setTenantDropdownOpen] = useState(false);
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  const handleManualCheck = async () => {
    setIsChecking(true);
    await checkConnection();
    setTimeout(() => setIsChecking(false), 600);
  };

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-sky-100 shadow-soft">
      {/* Top Utility Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs border-b border-sky-50">
        <div className="flex items-center gap-3">
          {/* Backend Status Badge */}
          <button
            onClick={handleManualCheck}
            title="Click to probe FastAPI server at http://localhost:8000"
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium transition-all ${
              isBackendOnline
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendOnline
                  ? 'bg-emerald-500 animate-pulse'
                  : 'bg-sky-400'
              }`}
            />
            <span>{isBackendOnline ? 'FastAPI Connected (:8000)' : 'API Sync Standby (Live Stream)'}</span>
            <RefreshCw className={`w-3 h-3 text-sky-500 ml-0.5 ${isChecking ? 'animate-spin' : ''}`} />
          </button>

          {/* Quick Stats Pill */}
          <div className="hidden md:flex items-center gap-2 text-slate-500">
            <span className="flex items-center gap-1 text-sky-800 font-medium">
              <Activity className="w-3.5 h-3.5 text-sky-500" />
              Flow: <span className="text-slate-800 font-semibold">{telemetry.flow_rate} L/min</span>
            </span>
            <span className="text-sky-200">|</span>
            <span className="flex items-center gap-1 text-sky-800 font-medium">
              Inlet TDS: <span className="text-slate-800 font-semibold">{telemetry.tds_in} ppm</span>
            </span>
            <span className="text-sky-200">|</span>
            <span className="flex items-center gap-1 text-sky-800 font-medium">
              Permeate TDS: <span className="text-emerald-700 font-bold">{telemetry.tds_out} ppm</span>
            </span>
          </div>
        </div>

        {/* Interactive Video Demo Triggers */}
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-600 bg-sky-100/60 px-2 py-0.5 rounded">
            Demo Simulator:
          </span>

          {/* Pump Toggle */}
          <button
            onClick={togglePump}
            className={`px-2.5 py-1 rounded-lg font-medium flex items-center gap-1.5 transition-all shadow-sm ${
              telemetry.pump_running
                ? 'bg-sky-500 text-white hover:bg-sky-600'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Zap className={`w-3 h-3 ${telemetry.pump_running ? 'fill-current animate-bounce' : ''}`} />
            <span>Pump: {telemetry.pump_running ? 'RUNNING' : 'STANDBY'}</span>
          </button>

          {/* Simulate TDS Spike */}
          <button
            onClick={triggerTdsSpike}
            className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 rounded-lg font-medium flex items-center gap-1 transition-all"
            title="Inject an inlet water TDS spike to see adaptive RO response"
          >
            <span>⚡ Inject TDS Spike</span>
          </button>

          {/* Pause/Play Stream */}
          <button
            onClick={toggleSimulation}
            className="p-1 rounded-lg text-slate-500 hover:text-sky-600 hover:bg-sky-50 transition-colors"
            title={isSimulating ? 'Pause telemetry stream' : 'Resume telemetry stream'}
          >
            {isSimulating ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Main Navigation Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between gap-4">
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-6">
          <NavLink to="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-sky-400 flex items-center justify-center text-white shadow-md shadow-sky-500/20 group-hover:scale-105 transition-transform">
              <Droplets className="w-6 h-6 animate-pulse-subtle" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-sky-700 to-sky-500 bg-clip-text text-transparent">
                  PureCast
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-sky-100 text-sky-700 uppercase tracking-wider">
                  Prognostics
                </span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">IoT Filter-Health Advisory Platform</p>
            </div>
          </NavLink>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center gap-1 ml-4">
            <NavLink
              to="/dashboard"
              end
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
                  isActive
                    ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/20'
                    : 'text-slate-600 hover:text-sky-600 hover:bg-sky-50'
                }`
              }
            >
              <Home className="w-4 h-4" />
              <span>Overview</span>
            </NavLink>

            <NavLink
              to="/dashboard/devices"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
                  isActive
                    ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/20'
                    : 'text-slate-600 hover:text-sky-600 hover:bg-sky-50'
                }`
              }
            >
              <Cpu className="w-4 h-4" />
              <span>Purifier Fleet</span>
            </NavLink>

            <NavLink
              to="/dashboard/analytics"
              className={({ isActive }) =>
                `px-3.5 py-2 rounded-xl text-sm font-semibold flex items-center gap-2 transition-all ${
                  isActive
                    ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/20'
                    : 'text-slate-600 hover:text-sky-600 hover:bg-sky-50'
                }`
              }
            >
              <LineChart className="w-4 h-4" />
              <span>ML Forecasting</span>
            </NavLink>
          </nav>
        </div>

        {/* Right Controls: Device Selector, Tenant, Role */}
        <div className="flex items-center gap-3">
          {/* Device Quick Switcher */}
          <div className="relative">
            <button
              onClick={() => setDeviceDropdownOpen(!deviceDropdownOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-sky-200 bg-sky-50/70 hover:bg-sky-100/70 text-slate-800 text-xs font-semibold transition-all shadow-sm"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <div className="text-left">
                <span className="block text-[10px] text-sky-600 font-bold uppercase">Active Purifier</span>
                <span className="truncate max-w-[120px] sm:max-w-[160px] block">{selectedDevice.serial_number}</span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-sky-500 ml-1" />
            </button>

            {deviceDropdownOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-float border border-sky-100 py-2 z-50 animate-in fade-in zoom-in-95">
                <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Select Purifier Unit
                </div>
                {devices.map((dev) => (
                  <button
                    key={dev.id}
                    onClick={() => {
                      setSelectedDevice(dev);
                      setDeviceDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3.5 py-2.5 flex items-center justify-between text-xs hover:bg-sky-50 transition-colors ${
                      dev.id === selectedDevice.id ? 'bg-sky-50/80 font-bold text-sky-900' : 'text-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-900">{dev.serial_number}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-sky-100 text-sky-700 font-bold">
                          {dev.device_tier}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{dev.model_name}</div>
                      <div className="text-[10px] text-sky-600 mt-0.5">{dev.household_name}</div>
                    </div>
                    {dev.id === selectedDevice.id && <Check className="w-4 h-4 text-sky-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Tenant Switcher */}
          <div className="relative hidden lg:block">
            <button
              onClick={() => setTenantDropdownOpen(!tenantDropdownOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium transition-all"
            >
              <Building2 className="w-3.5 h-3.5 text-sky-500" />
              <span className="max-w-[130px] truncate">{tenant.name}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {tenantDropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-float border border-sky-100 py-2 z-50">
                <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  OEM Tenant Switcher
                </div>
                {DEMO_TENANTS.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => {
                      setTenant(t);
                      setTenantDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3.5 py-2 flex items-center justify-between text-xs hover:bg-sky-50 ${
                      t.id === tenant.id ? 'bg-sky-50 text-sky-700 font-semibold' : 'text-slate-700'
                    }`}
                  >
                    <span>{t.name}</span>
                    {t.id === tenant.id && <Check className="w-3.5 h-3.5 text-sky-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Role Pill Switcher */}
          <div className="relative">
            <button
              onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
              className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-xl bg-gradient-to-r from-sky-50 to-white border border-sky-200 hover:border-sky-300 transition-all text-xs font-semibold text-slate-800"
            >
              <div className="w-6 h-6 rounded-lg bg-sky-500 text-white flex items-center justify-center text-xs font-bold shadow-xs">
                {user.full_name.charAt(0)}
              </div>
              <div className="text-left hidden sm:block">
                <span className="block text-[10px] text-slate-500 leading-none">{user.role.replace('_', ' ')}</span>
                <span className="block text-xs font-semibold text-slate-800 leading-tight truncate max-w-[100px]">
                  {user.full_name.split(' ')[0]}
                </span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </button>

            {roleDropdownOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-float border border-sky-100 py-2 z-50">
                <div className="px-3 py-1.5 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  Switch Persona (Demo View)
                </div>
                {Object.entries(DEMO_USERS).map(([key, u]) => (
                  <button
                    key={key}
                    onClick={() => {
                      setUser(u);
                      setRoleDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3.5 py-2.5 hover:bg-sky-50 flex items-center justify-between text-xs ${
                      u.id === user.id ? 'bg-sky-50 text-sky-800 font-semibold' : 'text-slate-700'
                    }`}
                  >
                    <div>
                      <div className="font-semibold text-slate-900">{u.full_name}</div>
                      <div className="text-[10px] text-slate-500">{u.role.replace('_', ' ')}</div>
                    </div>
                    {u.id === user.id && <Check className="w-3.5 h-3.5 text-sky-600" />}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

