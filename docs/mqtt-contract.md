# PureCast MQTT Protocol Specification (v1)

## 1. Overview
The PureCast edge purifier communicates with the cloud broker using MQTT (Port 1883 in dev, 8883 over TLS in production).
The system is strictly **ADVISORY ONLY**. The platform forecasts cartridge remaining useful life and diagnoses failure modes.

## 2. Topic Hierarchy
All topics are namespaced by tenant and device identifier:
```
purecast/{tenant_id}/{device_id}/telemetry
purecast/{tenant_id}/{device_id}/status
purecast/{tenant_id}/{device_id}/events
```

- Ingestion wildcard pattern: `purecast/+/+/+`

---

## 3. Telemetry Payload (`/telemetry`)
Versioned with `"v": 1`. Supports single sample or batched backfill readings.

### 3.1 Single Sample Format
```json
{
  "v": 1,
  "ts": 1772000000,
  "seq": 1042,
  "pump": true,
  "mode": "RO",
  "p1": 52.4,
  "p2": 45.1,
  "p3": 44.0,
  "flow_drain": 0.40,
  "flow_permeate": 1.15,
  "tds_in": 520.0,
  "tds_out": 12.0,
  "temp": 24.5,
  "ntu": 0.8,
  "uv_current": 395.0,
  "litres_delta": 0.19,
  "sig": "3f8a4e8d2c9b..."
}
```

### 3.2 Field Definitions
- `v`: integer, fixed `1`.
- `ts`: integer, UNIX epoch timestamp (seconds).
- `seq`: integer, monotonically increasing sequence number per device.
- `pump`: boolean (`true` / `false`), booster pump status.
- `mode`: string enum, operating mode: `"RO"`, `"UF_UV"`, or `"VACAY"`. Default: `"RO"`.
- `p1`: float, pre-filter inlet pressure (psi) [optional].
- `p2`: float, pre-filter outlet / post-carbon pressure (psi) [optional].
- `p3`: float, RO membrane feed driving pressure (psi) [optional].
- `flow_drain`: float, reject / brine drain flow rate (L/min) [optional].
- `flow_permeate`: float, product purified permeate flow rate (L/min) [optional].
- `tds_in`: float, feed raw water Total Dissolved Solids (ppm) [optional].
- `tds_out`: float, permeate purified water Total Dissolved Solids (ppm) [optional].
- `temp`: float, feed water temperature (°C) [optional].
- `ntu`: float, feed water turbidity (NTU) [optional].
- `uv_current`: float, UV disinfection lamp ballast current (mA) [optional].
- `litres_delta`: float, incremental liters produced during sampling interval [optional].
- `sig`: string, hex-encoded HMAC-SHA256 signature [optional].

### 3.3 LITE Device Tier
For software-only / LITE tier purifiers lacking pressure and turbidity transducers:
- Mandatory: `v`, `ts`, `seq`, `pump`, `tds_in`, `tds_out`, `litres_delta`.
- Omitted / null: `p1`, `p2`, `p3`, `flow_drain`, `flow_permeate`, `ntu`, `uv_current`.

### 3.4 Batch Backfill Format
When purifiers reconnect after network loss, buffered readings can be sent in a batch:
```json
{
  "v": 1,
  "batch": [
    { "ts": 1771999900, "seq": 1040, "pump": true, "tds_in": 515.0, "tds_out": 11.5, "litres_delta": 0.20 },
    { "ts": 1771999960, "seq": 1041, "pump": true, "tds_in": 518.0, "tds_out": 12.0, "litres_delta": 0.20 }
  ],
  "sig": "9a2f4..."
}
```

---

## 4. Status Payload (`/status`)
Communicates edge connectivity and health:
```json
{
  "status": "ONLINE",
  "ts": 1772000000,
  "firmware": "v1.2.0",
  "ip": "192.168.1.100",
  "rssi": -65
}
```
Valid statuses: `"ONLINE"`, `"OFFLINE"`, `"DEGRADED"`, `"MAINTENANCE"`.

---

## 5. Events Payload (`/events`)
Notifies backend of contextual external occurrences:
```json
{
  "event_type": "POWER_CUT",
  "ts": 1772000000,
  "description": "Auxiliary capacitor detected loss of AC main voltage",
  "metadata": { "duration_sec": 300 }
}
```
Event types: `"POWER_CUT"`, `"HOLIDAY"`, `"COLD_WATER_MORNING"`, `"FILTER_REPLACED"`.

---

## 6. Authentication & Replay Protection
1. **Tenant Integrity**: The `tenant_id` extracted from the MQTT topic must match the registered tenant of the `device_id`.
2. **Replay Protection**:
   - Packets with `ts > now + 600` (more than 10 minutes in the future) are rejected.
   - Sequence deduplication: Duplicate `(device_id, seq)` pairs are cached in Redis with a 24-hour TTL and rejected upon duplicate arrival.
3. **HMAC-SHA256 Signature**:
   - Optional field `"sig"`. If the device has a configured shared secret in `device_credentials`, the ingestor validates `sig == HMAC-SHA256(secret, canonical_payload_without_sig)`.
