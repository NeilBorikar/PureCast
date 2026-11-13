import axios from 'axios';
import { Device, FilterCartridge, LiveTelemetry, DiagnosticAlert, User, Tenant } from '../types';

const API_BASE_URL = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 4000,
});

// Attach JWT access token if stored
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('purecast_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Demo Tenants
export const DEMO_TENANTS: Tenant[] = [
  {
    id: 't-atomberg-101',
    name: 'Atomberg Technologies',
    slug: 'atomberg',
    tier: 'FULL',
  },
  {
    id: 't-aquaguard-202',
    name: 'Aquaguard OEM Services',
    slug: 'aquaguard',
    tier: 'FULL',
  },
];

// Demo Users
export const DEMO_USERS: Record<string, User> = {
  admin: {
    id: 'u-admin-01',
    email: 'admin@atomberg.com',
    full_name: 'Aditya Roy (Operations Lead)',
    role: 'TENANT_ADMIN',
    tenant_id: 't-atomberg-101',
  },
  technician: {
    id: 'u-tech-02',
    email: 'tech1@atomberg.com',
    full_name: 'Ramesh Patel (Senior Field Tech)',
    role: 'SERVICE_TECHNICIAN',
    tenant_id: 't-atomberg-101',
  },
  customer: {
    id: 'u-cust-03',
    email: 'customer1@gmail.com',
    full_name: 'Priya Sharma (Household Owner)',
    role: 'HOUSEHOLD_OWNER',
    tenant_id: 't-atomberg-101',
  },
};

// Initial Demo Devices
export const INITIAL_DEVICES: Device[] = [
  {
    id: 'dev-atm-001',
    tenant_id: 't-atomberg-101',
    household_id: 'hh-01',
    household_name: 'Sharma Residence',
    household_address: 'Flat 402, Lotus Tower, Powai, Mumbai',
    serial_number: 'ATM-X1-001',
    device_tier: 'FULL',
    model_name: 'AtomPure-X1 Pro Smart RO',
    operating_mode: 'RO',
    is_active: true,
    installed_at: '2026-03-15T10:00:00Z',
    cartridges: [
      {
        id: 'c-sed-01',
        consumable_type: 'SEDIMENT',
        serial_number: 'CRT-SED-901',
        model_number: 'MOD-SED-2026',
        current_health_percentage: 64.5,
        remaining_days: 42,
        band_low: 38,
        band_high: 46,
        status_text: 'REPLACE_SOON',
        liters_filtered: 4250,
        rated_capacity_liters: 6000,
        installed_at: '2026-03-15T10:00:00Z',
        wear_rate_per_day: 0.85,
      },
      {
        id: 'c-carb-02',
        consumable_type: 'CARBON',
        serial_number: 'CRT-CAR-902',
        model_number: 'MOD-CAR-2026',
        current_health_percentage: 82.0,
        remaining_days: 118,
        band_low: 110,
        band_high: 126,
        status_text: 'OPTIMAL',
        liters_filtered: 2840,
        rated_capacity_liters: 6000,
        installed_at: '2026-03-15T10:00:00Z',
        wear_rate_per_day: 0.42,
      },
      {
        id: 'c-mem-prot-03',
        consumable_type: 'MEMBRANE_PROTECTOR',
        serial_number: 'CRT-MEM-903',
        model_number: 'MOD-MEM-2026',
        current_health_percentage: 89.2,
        remaining_days: 195,
        band_low: 185,
        band_high: 205,
        status_text: 'OPTIMAL',
        liters_filtered: 1960,
        rated_capacity_liters: 6000,
        installed_at: '2026-03-15T10:00:00Z',
        wear_rate_per_day: 0.28,
      },
      {
        id: 'c-ro-04',
        consumable_type: 'RO_MEMBRANE',
        serial_number: 'CRT-RO-904',
        model_number: 'MOD-RO-2026',
        current_health_percentage: 93.8,
        remaining_days: 285,
        band_low: 270,
        band_high: 300,
        status_text: 'OPTIMAL',
        liters_filtered: 1220,
        rated_capacity_liters: 7500,
        installed_at: '2026-03-15T10:00:00Z',
        wear_rate_per_day: 0.18,
      },
      {
        id: 'c-uv-05',
        consumable_type: 'UV_LAMP',
        serial_number: 'CRT-UV-905',
        model_number: 'MOD-UV-2026',
        current_health_percentage: 86.4,
        remaining_days: 172,
        band_low: 160,
        band_high: 184,
        status_text: 'OPTIMAL',
        liters_filtered: 2100,
        rated_capacity_liters: 6000,
        installed_at: '2026-03-15T10:00:00Z',
        wear_rate_per_day: 0.35,
      },
    ],
  },
  {
    id: 'dev-atm-002',
    tenant_id: 't-atomberg-101',
    household_id: 'hh-02',
    household_name: 'Mehta Penthouse',
    household_address: '14B, Altamount Road, South Mumbai',
    serial_number: 'ATM-LT-002',
    device_tier: 'LITE',
    model_name: 'AtomPure-Lite Urban RO',
    operating_mode: 'ECO',
    is_active: true,
    installed_at: '2026-06-10T11:30:00Z',
    cartridges: [
      {
        id: 'c-sed-02',
        consumable_type: 'SEDIMENT',
        serial_number: 'CRT-SED-880',
        model_number: 'MOD-SED-2026',
        current_health_percentage: 88.0,
        remaining_days: 180,
        band_low: 170,
        band_high: 190,
        status_text: 'OPTIMAL',
        liters_filtered: 1200,
        rated_capacity_liters: 6000,
        installed_at: '2026-06-10T11:30:00Z',
        wear_rate_per_day: 0.32,
      },
      {
        id: 'c-ro-05',
        consumable_type: 'RO_MEMBRANE',
        serial_number: 'CRT-RO-881',
        model_number: 'MOD-RO-2026',
        current_health_percentage: 95.0,
        remaining_days: 310,
        band_low: 295,
        band_high: 325,
        status_text: 'OPTIMAL',
        liters_filtered: 850,
        rated_capacity_liters: 7500,
        installed_at: '2026-06-10T11:30:00Z',
        wear_rate_per_day: 0.14,
      },
    ],
  },
  {
    id: 'dev-aqm-101',
    tenant_id: 't-aquaguard-202',
    household_id: 'hh-03',
    household_name: 'Verma Residence',
    household_address: 'Villa 18, Sector 15, Gurgaon, NCR',
    serial_number: 'AQM-PRO-101',
    device_tier: 'FULL',
    model_name: 'AquaMax Pro Plus Industrial RO',
    operating_mode: 'RO',
    is_active: true,
    installed_at: '2026-01-20T09:15:00Z',
    cartridges: [
      {
        id: 'c-sed-03',
        consumable_type: 'SEDIMENT',
        serial_number: 'CRT-SED-550',
        model_number: 'MOD-SED-2026',
        current_health_percentage: 24.0,
        remaining_days: 9,
        band_low: 7,
        band_high: 11,
        status_text: 'REPLACE_SOON',
        liters_filtered: 5600,
        rated_capacity_liters: 6000,
        installed_at: '2026-01-20T09:15:00Z',
        wear_rate_per_day: 1.15,
      },
      {
        id: 'c-carb-03',
        consumable_type: 'CARBON',
        serial_number: 'CRT-CAR-551',
        model_number: 'MOD-CAR-2026',
        current_health_percentage: 58.0,
        remaining_days: 64,
        band_low: 58,
        band_high: 70,
        status_text: 'DEGRADED',
        liters_filtered: 4200,
        rated_capacity_liters: 6000,
        installed_at: '2026-01-20T09:15:00Z',
        wear_rate_per_day: 0.65,
      },
      {
        id: 'c-ro-06',
        consumable_type: 'RO_MEMBRANE',
        serial_number: 'CRT-RO-552',
        model_number: 'MOD-RO-2026',
        current_health_percentage: 79.5,
        remaining_days: 140,
        band_low: 130,
        band_high: 150,
        status_text: 'OPTIMAL',
        liters_filtered: 3100,
        rated_capacity_liters: 7500,
        installed_at: '2026-01-20T09:15:00Z',
        wear_rate_per_day: 0.38,
      },
    ],
  },
];

export const INITIAL_TELEMETRY: LiveTelemetry = {
  timestamp: new Date().toISOString(),
  pump_running: true,
  pressure_p1: 2.85,
  pressure_p2: 2.15,
  pressure_p3: 0.32,
  flow_rate: 1.85,
  tds_in: 745,
  tds_out: 38,
  temperature: 25.8,
  turbidity: 0.35,
  uv_current: 418,
  today_liters: 14.2,
};

export const INITIAL_ALERTS: DiagnosticAlert[] = [
  {
    id: 'alt-01',
    fault_type: 'FILTER_EXPIRING_SOON',
    severity: 'medium',
    confidence: 0.94,
    human_text: 'Sediment Filter wear rate accelerating due to elevated municipal turbidity. Replacement recommended within 42 days.',
    evidence: {
      consumable: 'SEDIMENT',
      current_turbidity: 0.35,
      baseline_wear_delta: '+24%',
    },
    timestamp: '12 mins ago',
  },
  {
    id: 'alt-02',
    fault_type: 'OPTIMAL_RO_REJECTION',
    severity: 'low',
    confidence: 0.99,
    human_text: 'RO Membrane rejection efficiency is 94.9% (745 ppm in -> 38 ppm out). Mineral taste profile verified.',
    evidence: {
      tds_in: 745,
      tds_out: 38,
      rejection_percentage: 94.9,
    },
    timestamp: '35 mins ago',
  },
];

// Backend Health Checker
export async function checkBackendHealth(): Promise<{ online: boolean; version?: string }> {
  try {
    const res = await apiClient.get('/health');
    return { online: res.status === 200, version: res.data?.version || '0.1.0' };
  } catch (err) {
    return { online: false };
  }
}

// Fetch Devices with Fallback
export async function fetchDevices(): Promise<Device[]> {
  try {
    const res = await apiClient.get('/devices');
    if (res.data && Array.isArray(res.data) && res.data.length > 0) {
      // Merge with cartridge details if necessary
      return res.data;
    }
  } catch {
    // Graceful fallback to initial devices
  }
  return INITIAL_DEVICES;
}

// Post Telemetry Batch
export async function sendTelemetryReading(reading: Partial<LiveTelemetry>, deviceId: string): Promise<boolean> {
  try {
    await apiClient.post('/telemetry/batch', {
      device_id: deviceId,
      readings: [reading],
    });
    return true;
  } catch {
    // Handled locally
    return false;
  }
}

