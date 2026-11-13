import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Device, FilterCartridge, LiveTelemetry, DiagnosticAlert, User, Tenant } from '../types';
import {
  INITIAL_DEVICES,
  INITIAL_TELEMETRY,
  INITIAL_ALERTS,
  DEMO_USERS,
  DEMO_TENANTS,
  checkBackendHealth,
  sendTelemetryReading,
} from '../services/api';

interface Toast {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message: string;
}

interface AppContextType {
  user: User;
  setUser: (u: User) => void;
  tenant: Tenant;
  setTenant: (t: Tenant) => void;
  devices: Device[];
  selectedDevice: Device;
  setSelectedDevice: (d: Device) => void;
  telemetry: LiveTelemetry;
  setTelemetry: React.Dispatch<React.SetStateAction<LiveTelemetry>>;
  alerts: DiagnosticAlert[];
  isBackendOnline: boolean;
  checkConnection: () => Promise<void>;
  toasts: Toast[];
  addToast: (t: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  reorderCartridge: (cartridge: FilterCartridge) => void;
  isSimulating: boolean;
  toggleSimulation: () => void;
  triggerTdsSpike: () => void;
  togglePump: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [tenant, setTenant] = useState<Tenant>(DEMO_TENANTS[0]);
  const [user, setUser] = useState<User>(DEMO_USERS.admin);
  const [devices, setDevices] = useState<Device[]>(INITIAL_DEVICES);
  const [selectedDevice, setSelectedDevice] = useState<Device>(INITIAL_DEVICES[0]);
  const [telemetry, setTelemetry] = useState<LiveTelemetry>(INITIAL_TELEMETRY);
  const [alerts, setAlerts] = useState<DiagnosticAlert[]>(INITIAL_ALERTS);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(false);
  const [isSimulating, setIsSimulating] = useState<boolean>(true);
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Function to show toast
  const addToast = (t: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { ...t, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id));
    }, 4500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((item) => item.id !== id));
  };

  // Re-check backend connection
  const checkConnection = async () => {
    const res = await checkBackendHealth();
    setIsBackendOnline(res.online);
    if (res.online) {
      addToast({
        type: 'success',
        title: 'Backend Connected',
        message: 'PureCast FastAPI server is online & synchronized at :8000',
      });
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 15000);
    return () => clearInterval(interval);
  }, []);

  // Update selected device if tenant changes
  useEffect(() => {
    const matching = devices.filter((d) => d.tenant_id === tenant.id);
    if (matching.length > 0 && !matching.some((m) => m.id === selectedDevice.id)) {
      setSelectedDevice(matching[0]);
    }
  }, [tenant, devices]);

  // Telemetry real-time pulse simulation
  useEffect(() => {
    if (!isSimulating) return;

    const interval = setInterval(() => {
      setTelemetry((prev) => {
        if (!prev.pump_running) {
          return {
            ...prev,
            flow_rate: 0,
            pressure_p1: +(prev.pressure_p1 * 0.95).toFixed(2),
            pressure_p2: 0.1,
            pressure_p3: 0.05,
            timestamp: new Date().toISOString(),
          };
        }

        // Slight micro-variations for live water flow feel
        const p1 = +(2.8 + (Math.random() * 0.2 - 0.1)).toFixed(2);
        const p2 = +(2.1 + (Math.random() * 0.1 - 0.05)).toFixed(2);
        const flow = +(1.8 + (Math.random() * 0.1 - 0.05)).toFixed(2);
        const addedLiters = +(prev.today_liters + 0.005).toFixed(2);

        const newTele: LiveTelemetry = {
          ...prev,
          pressure_p1: p1,
          pressure_p2: p2,
          flow_rate: flow,
          today_liters: addedLiters,
          timestamp: new Date().toISOString(),
        };

        // If backend is online, optionally stream to endpoint
        if (isBackendOnline && selectedDevice) {
          sendTelemetryReading(newTele, selectedDevice.id);
        }

        return newTele;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, [isSimulating, isBackendOnline, selectedDevice]);

  // Reorder Cartridge Action
  const reorderCartridge = (cartridge: FilterCartridge) => {
    // Optimistically update status
    setSelectedDevice((prevDev) => {
      const updatedCartridges = prevDev.cartridges.map((c) => {
        if (c.id === cartridge.id) {
          return {
            ...c,
            status_text: 'OPTIMAL' as const,
            current_health_percentage: 100,
            remaining_days: 365,
            liters_filtered: 0,
          };
        }
        return c;
      });
      return { ...prevDev, cartridges: updatedCartridges };
    });

    addToast({
      type: 'success',
      title: 'Cartridge Dispatched!',
      message: `Fresh ${cartridge.consumable_type.replace('_', ' ')} (${cartridge.model_number}) ordered. Priority delivery by Ramesh Patel scheduled.`,
    });
  };

  // Simulation Controls
  const toggleSimulation = () => {
    setIsSimulating((prev) => !prev);
    addToast({
      type: 'info',
      title: 'Telemetry Simulation',
      message: isSimulating ? 'Sensor telemetry stream paused' : 'Real-time water flow telemetry active',
    });
  };

  const togglePump = () => {
    setTelemetry((prev) => {
      const nextPump = !prev.pump_running;
      addToast({
        type: nextPump ? 'info' : 'warning',
        title: nextPump ? 'Pump Started' : 'Pump Stopped',
        message: nextPump ? 'Dispensing purified water (1.8 L/min)' : 'Purifier in standby mode',
      });
      return {
        ...prev,
        pump_running: nextPump,
        flow_rate: nextPump ? 1.85 : 0,
      };
    });
  };

  const triggerTdsSpike = () => {
    setTelemetry((prev) => ({
      ...prev,
      tds_in: 960,
      tds_out: 48,
      turbidity: 0.85,
    }));

    const spikeAlert: DiagnosticAlert = {
      id: `alt-${Date.now()}`,
      fault_type: 'HIGH_INLET_TDS_SPIKE',
      severity: 'high',
      confidence: 0.98,
      human_text: 'Sudden spike detected in municipal water TDS (960 ppm). RO High-Pressure booster engaged; rejection held at 95.0%.',
      evidence: { tds_in: 960, tds_out: 48, threshold: 800 },
      timestamp: 'Just now',
    };

    setAlerts((prev) => [spikeAlert, ...prev]);

    addToast({
      type: 'warning',
      title: 'Inlet TDS Spike (960 ppm)!',
      message: 'Adaptive multi-stage filtration dynamically compensated to maintain drinking purity.',
    });
  };

  return (
    <AppContext.Provider
      value={{
        user,
        setUser,
        tenant,
        setTenant,
        devices,
        selectedDevice,
        setSelectedDevice,
        telemetry,
        setTelemetry,
        alerts,
        isBackendOnline,
        checkConnection,
        toasts,
        addToast,
        removeToast,
        reorderCartridge,
        isSimulating,
        toggleSimulation,
        triggerTdsSpike,
        togglePump,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

