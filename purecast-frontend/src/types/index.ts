export type ConsumableType =
  | 'SEDIMENT'
  | 'CARBON'
  | 'MEMBRANE_PROTECTOR'
  | 'RO_MEMBRANE'
  | 'UV_LAMP';

export type DeviceTier = 'FULL' | 'LITE';

export type OperatingMode = 'RO' | 'UV' | 'BYPASS' | 'ECO';

export type UserRole =
  | 'PLATFORM_ADMIN'
  | 'TENANT_ADMIN'
  | 'TENANT_ANALYST'
  | 'SERVICE_TECHNICIAN'
  | 'HOUSEHOLD_OWNER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  tenant_id: string;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  tier: string;
}

export interface Household {
  id: string;
  name: string;
  address: string;
  tenant_id: string;
}

export interface FilterCartridge {
  id: string;
  consumable_type: ConsumableType;
  serial_number: string;
  model_number: string;
  current_health_percentage: number;
  remaining_days: number;
  band_low: number;
  band_high: number;
  status_text: 'OPTIMAL' | 'DEGRADED' | 'REPLACE_SOON' | 'EXHAUSTED';
  liters_filtered: number;
  rated_capacity_liters: number;
  installed_at: string;
  wear_rate_per_day: number;
}

export interface Device {
  id: string;
  tenant_id: string;
  household_id?: string;
  household_name?: string;
  household_address?: string;
  serial_number: string;
  device_tier: DeviceTier;
  model_name: string;
  operating_mode: OperatingMode;
  is_active: boolean;
  installed_at: string;
  cartridges: FilterCartridge[];
}

export interface LiveTelemetry {
  timestamp: string;
  pump_running: boolean;
  pressure_p1: number; // Inlet bar
  pressure_p2: number; // Pre-RO bar
  pressure_p3: number; // Permeate bar
  flow_rate: number;   // L/min
  tds_in: number;      // ppm
  tds_out: number;     // ppm
  temperature: number; // °C
  turbidity: number;   // NTU
  uv_current: number;  // mA
  today_liters: number;
}

export interface DiagnosticAlert {
  id: string;
  fault_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  human_text: string;
  evidence: Record<string, any>;
  timestamp: string;
}

