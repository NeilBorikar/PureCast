import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Device } from '../types';
import {
  Cpu,
  Search,
  Plus,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ShieldCheck,
  Calendar,
  Layers,
  Filter,
} from 'lucide-react';

export const DevicesPage: React.FC = () => {
  const { devices, setSelectedDevice, tenant, addToast } = useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTier, setSelectedTier] = useState<string>('ALL');
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [newSerial, setNewSerial] = useState('');
  const [newModel, setNewModel] = useState('');
  const [newHousehold, setNewHousehold] = useState('');
  const navigate = useNavigate();

  const filteredDevices = devices.filter((d) => {
    const matchesSearch =
      d.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.model_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (d.household_name && d.household_name.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesTier = selectedTier === 'ALL' || d.device_tier === selectedTier;
    return matchesSearch && matchesTier;
  });

  const handleSelectDevice = (dev: Device) => {
    setSelectedDevice(dev);
    navigate('/dashboard');
    addToast({
      type: 'info',
      title: 'Active Purifier Switched',
      message: `Now viewing diagnostics for ${dev.serial_number} (${dev.model_name}).`,
    });
  };

  const handleRegisterDevice = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSerial || !newModel) return;

    addToast({
      type: 'success',
      title: 'Purifier Registered',
      message: `Unit ${newSerial} (${newModel}) provisioned with edge credentials.`,
    });
    setIsRegisterModalOpen(false);
    setNewSerial('');
    setNewModel('');
    setNewHousehold('');
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Cpu className="w-6 h-6 text-sky-600" />
            Purifier Fleet Management
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Registered telemetry-enabled water purification units for{' '}
            <span className="font-semibold text-slate-700">{tenant.name}</span>
          </p>
        </div>

        <button
          onClick={() => setIsRegisterModalOpen(true)}
          className="px-4 py-2.5 rounded-2xl bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold transition-all flex items-center gap-2 shadow-sm shadow-sky-600/20"
        >
          <Plus className="w-4 h-4" />
          <span>Provision New Purifier</span>
        </button>
      </div>

      {/* Fleet Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-sky-100 shadow-card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-black text-lg border border-sky-100">
            {devices.length}
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium block">Total Fleet Devices</span>
            <div className="text-lg font-black text-slate-900 mt-0.5">Connected IoT Units</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-sky-100 shadow-card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-black text-lg border border-emerald-100">
            {devices.filter((d) => d.is_active).length}
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium block">Active Telemetry Stream</span>
            <div className="text-lg font-black text-emerald-700 mt-0.5">100% Operational</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-sky-100 shadow-card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-black text-lg border border-amber-100">
            1
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium block">Advisories Pending</span>
            <div className="text-lg font-black text-amber-700 mt-0.5">Sediment Filter Action</div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-2xl border border-sky-100 shadow-card flex flex-wrap items-center justify-between gap-3">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by serial number, model, or customer household..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-sky-50/50 border border-sky-100 text-xs focus:outline-none focus:border-sky-400 focus:bg-white text-slate-800 placeholder:text-slate-400"
          />
        </div>

        <div className="flex items-center gap-2">
          {['ALL', 'FULL', 'LITE'].map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedTier(tier)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                selectedTier === tier
                  ? 'bg-sky-500 text-white shadow-xs'
                  : 'bg-sky-50 text-slate-600 hover:bg-sky-100'
              }`}
            >
              {tier === 'ALL' ? 'All Tiers' : `${tier} Tier`}
            </button>
          ))}
        </div>
      </div>

      {/* Device Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredDevices.map((dev) => {
          const avgHealth = Math.round(
            dev.cartridges.reduce((acc, c) => acc + c.current_health_percentage, 0) /
              (dev.cartridges.length || 1)
          );

          return (
            <div
              key={dev.id}
              className="bg-white rounded-3xl border border-sky-100 p-6 shadow-card hover:shadow-float hover:border-sky-300 transition-all flex flex-col justify-between"
            >
              <div>
                {/* Header */}
                <div className="flex items-center justify-between gap-2 mb-3">
                  <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-700 font-mono">
                    {dev.serial_number}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 uppercase">
                      {dev.device_tier}
                    </span>
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  </div>
                </div>

                <h3 className="font-extrabold text-slate-900 text-base leading-snug">
                  {dev.model_name}
                </h3>

                <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-2">
                  <MapPin className="w-3.5 h-3.5 text-sky-500 flex-shrink-0" />
                  <span className="truncate">{dev.household_name} • {dev.household_address}</span>
                </div>

                {/* Overall Health Metric */}
                <div className="my-5 p-4 rounded-2xl bg-gradient-to-r from-sky-50/70 to-white border border-sky-100">
                  <div className="flex justify-between items-center mb-1.5 text-xs">
                    <span className="font-semibold text-slate-600">Average Filter Health</span>
                    <span className="font-extrabold text-sky-900">{avgHealth}%</span>
                  </div>
                  <div className="w-full h-2 bg-sky-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${
                        avgHealth > 60 ? 'bg-sky-500' : 'bg-amber-500'
                      }`}
                      style={{ width: `${avgHealth}%` }}
                    />
                  </div>

                  {/* Individual Cartridge Health Chips */}
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {dev.cartridges.map((c) => (
                      <span
                        key={c.id}
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${
                          c.current_health_percentage > 50
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}
                      >
                        {c.consumable_type.slice(0, 3)}: {Math.round(c.current_health_percentage)}%
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => handleSelectDevice(dev)}
                className="w-full py-2.5 px-4 rounded-2xl bg-sky-50 hover:bg-sky-500 hover:text-white text-sky-700 border border-sky-200 hover:border-transparent text-xs font-bold transition-all flex items-center justify-center gap-2 group"
              >
                <span>Inspect Diagnostics & Telemetry</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          );
        })}
      </div>

      {/* Provision New Purifier Modal */}
      {isRegisterModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-float border border-sky-100 animate-in fade-in zoom-in-95">
            <h2 className="text-lg font-black text-slate-900 mb-1">Provision New Purifier</h2>
            <p className="text-xs text-slate-500 mb-4">
              Registers device serial on PureCast backend and generates HMAC edge keys.
            </p>

            <form onSubmit={handleRegisterDevice} className="space-y-3.5">
              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                  Serial Number
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. ATM-X1-003"
                  value={newSerial}
                  onChange={(e) => setNewSerial(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-sky-100 text-xs focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                  Model Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. AtomPure Pro 2026"
                  value={newModel}
                  onChange={(e) => setNewModel(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-sky-100 text-xs focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                  Assigned Household
                </label>
                <input
                  type="text"
                  placeholder="e.g. Kapoor Residence, Bandra"
                  value={newHousehold}
                  onChange={(e) => setNewHousehold(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-sky-100 text-xs focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setIsRegisterModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-sky-600 text-white text-xs font-bold hover:bg-sky-700 shadow-sm"
                >
                  Confirm & Provision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DevicesPage;

