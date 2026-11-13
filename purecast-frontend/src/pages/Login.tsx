import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { DEMO_USERS } from '../services/api';
import {
  Droplets,
  ShieldCheck,
  Lock,
  Mail,
  ArrowRight,
  Sparkles,
  UserCheck,
  Activity,
} from 'lucide-react';

export const Login: React.FC = () => {
  const { setUser, addToast, isBackendOnline } = useApp();
  const [email, setEmail] = useState('admin@atomberg.com');
  const [password, setPassword] = useState('DemoPassword123!');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    setTimeout(() => {
      setIsLoading(false);
      // Select appropriate demo user
      const matchedUser =
        Object.values(DEMO_USERS).find((u) => u.email === email) || DEMO_USERS.admin;
      setUser(matchedUser);

      addToast({
        type: 'success',
        title: `Welcome, ${matchedUser.full_name}`,
        message: `Signed in as ${matchedUser.role.replace('_', ' ')} with prognostic telemetry permissions.`,
      });

      navigate('/dashboard');
    }, 600);
  };

  const handleQuickLogin = (userKey: keyof typeof DEMO_USERS) => {
    const selected = DEMO_USERS[userKey];
    setEmail(selected.email);
    setUser(selected);
    addToast({
      type: 'success',
      title: 'Demo Persona Activated',
      message: `Signed in as ${selected.full_name} (${selected.role.replace('_', ' ')}).`,
    });
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-sky-50 via-white to-sky-100 relative overflow-hidden">
      {/* Background Decorative Rings */}
      <div className="absolute top-1/4 -left-20 w-80 h-80 bg-sky-200/40 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-20 w-80 h-80 bg-sky-100/60 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full bg-white rounded-3xl border border-sky-100 p-8 shadow-float relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-600 to-sky-400 text-white shadow-md shadow-sky-500/30 mb-3 animate-pulse-subtle">
            <Droplets className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-black tracking-tight bg-gradient-to-r from-sky-800 to-sky-600 bg-clip-text text-transparent">
            PureCast
          </h1>
          <p className="text-xs text-slate-500 mt-1 font-medium">
            Next-Gen Water Purifier Prognostics & RUL Telemetry
          </p>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-50 border border-sky-200 text-[11px] font-semibold text-sky-700 mt-3">
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendOnline ? 'bg-emerald-500 animate-pulse' : 'bg-sky-400'
              }`}
            />
            <span>{isBackendOnline ? 'FastAPI Backend Live (:8000)' : 'Simulator Ready'}</span>
          </div>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Work Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-sky-100 bg-sky-50/40 focus:bg-white text-xs text-slate-800 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-sky-100 bg-sky-50/40 focus:bg-white text-xs text-slate-800 focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100 font-medium"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-600 to-sky-500 hover:from-sky-700 hover:to-sky-600 text-white text-xs font-bold transition-all shadow-md shadow-sky-600/20 flex items-center justify-center gap-2 group mt-2"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>Sign In to Telemetry Dashboard</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
        </form>

        {/* Quick Demo Personas (Ideal for Video Recording!) */}
        <div className="mt-8 pt-6 border-t border-sky-100">
          <div className="text-center text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">
            Quick 1-Click Demo Personas
          </div>
          <div className="space-y-2">
            <button
              onClick={() => handleQuickLogin('admin')}
              className="w-full p-2.5 rounded-xl border border-sky-100 bg-sky-50/60 hover:bg-sky-100/80 text-left text-xs transition-colors flex items-center justify-between"
            >
              <div>
                <span className="font-bold text-slate-900 block">Atomberg Admin</span>
                <span className="text-[10px] text-slate-500">Fleet Operations & Diagnostics</span>
              </div>
              <span className="text-[10px] font-bold text-sky-600 bg-white px-2 py-0.5 rounded border border-sky-200">
                Log In &rarr;
              </span>
            </button>

            <button
              onClick={() => handleQuickLogin('technician')}
              className="w-full p-2.5 rounded-xl border border-sky-100 bg-sky-50/60 hover:bg-sky-100/80 text-left text-xs transition-colors flex items-center justify-between"
            >
              <div>
                <span className="font-bold text-slate-900 block">Ramesh Tech (Field Technician)</span>
                <span className="text-[10px] text-slate-500">Cartridge Service & Replacement Dispatch</span>
              </div>
              <span className="text-[10px] font-bold text-sky-600 bg-white px-2 py-0.5 rounded border border-sky-200">
                Log In &rarr;
              </span>
            </button>

            <button
              onClick={() => handleQuickLogin('customer')}
              className="w-full p-2.5 rounded-xl border border-sky-100 bg-sky-50/60 hover:bg-sky-100/80 text-left text-xs transition-colors flex items-center justify-between"
            >
              <div>
                <span className="font-bold text-slate-900 block">Priya Sharma (Consumer)</span>
                <span className="text-[10px] text-slate-500">Household Kitchen Purifier Owner</span>
              </div>
              <span className="text-[10px] font-bold text-sky-600 bg-white px-2 py-0.5 rounded border border-sky-200">
                Log In &rarr;
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

