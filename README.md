# ChargeMesh

An EV infrastructure operating system for India's commercial EV market. ChargeMesh handles the full stack of a charging and battery-swap network: an OCPP 1.6 Central System for charge point management, a real-time telemetry pipeline, a Battery-as-a-Service (BaaS) settlement engine, a thermal stress monitor, and a dispatch recommendation system — plus a fleet dashboard and a driver mobile app.

Built specifically for the Indian commercial EV context: two-wheeler fleets, Indian OEMs (Ather, OLA Electric, TVS), Indian charging networks (Chargezone, Statiq), and LFP/NMC battery chemistries deployed at scale.

> **Status:** The software is feature-complete and runs in development mode with mock OEM and network integrations. Live OEM integrations require signed fleet API partnership agreements. Charging network integrations require B2B contracts with Chargezone/Statiq.

---

## What It Does

### OCPP 1.6 Central System
A full WebSocket-based Central System that charging stations connect to over `wss://`. Implements the OCPP 1.6 state machine at the connector level:

```
Available → Preparing → Charging → Finishing → Available
Available → Unavailable  (hardware fault)
Any       → Faulted
```

Handles `BootNotification`, `Heartbeat`, `StatusNotification`, `StartTransaction`, `StopTransaction`, and `MeterValues`. Heartbeat monitor runs every 60 seconds and marks stations offline after 3 minutes of silence.

### Battery-as-a-Service Settlement
Calculates per-swap settlement amounts between fleet operators and battery vendors:

```
kwh_cost         = kwh_consumed × price_per_kwh_inr
excess_degradation = max(0, actual_degradation - (threshold_pct × kwh_consumed / 100))
degradation_cost = excess_degradation × price_per_soh_point_inr
total            = kwh_cost + degradation_cost
```

Monthly settlement reports aggregate all swaps for a fleet/vendor pair over a billing period. Pricing configs are per fleet × vendor × battery model, time-bounded, and hot-swappable without redeploy.

### Battery Degradation Model
Capacity fade model calibrated for Indian commercial EV conditions (LFP and NMC chemistries):

```
SoH = 100 - (cycle_degradation + thermal_degradation + dod_degradation)

cycle_degradation   = cycle_count × base_rate_per_cycle
                      (LFP: 0.025%/cycle, NMC: 0.05%/cycle)
thermal_degradation = accumulated_thermal_stress × 0.01%/degree-hour
dod_degradation     = deep_discharge_count × chemistry_penalty
```

Thermal stress index accumulates degree-hours above 35°C (LFP/NMC thermal comfort baseline). Batteries exceeding 200 degree-hours are automatically flagged for inspection.

### Dispatch Engine
Triggers a charging recommendation when:
- SoC < 25% AND estimated range < (remaining delivery km + 10 km safety buffer)

Finds the nearest available charging station using Haversine distance within a 15 km radius, filters to operational stations with available connectors, and records a `DispatchRecommendation` with predicted depletion time.

### Thermal Monitoring
Two alert levels:
- **Warning (>42°C):** Alert created; de-duplicated within a 2-hour window
- **Critical (>48°C):** Alert created + push notification queued via Celery

Celery Beat task runs every 10 minutes to promote unresolved warning alerts to `sustained_high_temp` after 30 minutes.

---

## Architecture

```
                      Fleet Operators / Drivers
                              |
              +---------------+---------------+
              |                               |
              v                               v
     Next.js Dashboard                React Native App
       (port 3000)                    (Expo / bare)
              |                               |
              v                               v
        FastAPI REST API (port 8000)
              |
    +---------+---------+-----------+
    |         |         |           |
    v         v         v           v
PostgreSQL  Redis    Celery      MQTT Broker
            (broker) Worker      (Mosquitto)
                        |              |
                        v              v
                 Async tasks    OEM telemetry
                 (settlement,   (paho-mqtt)
                  thermal,
                  dispatch)

              Charging Stations
                    |
                    v (WebSocket / OCPP 1.6)
           OCPP Central System (port 9000)
                    |
                    v
             PostgreSQL (shared DB)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.111, Python 3.12 |
| OCPP Server | `ocpp` 0.19, `websockets` 12 |
| MQTT | `paho-mqtt` 2.0, Mosquitto |
| Task Queue | Celery 5.4 + Redis |
| Database | PostgreSQL 16 + SQLAlchemy (async) + Alembic |
| Auth | JWT (python-jose), Fernet encryption at rest |
| Fleet Dashboard | Next.js 14, Tailwind CSS |
| Driver App | React Native (Expo), TypeScript |
| Containerisation | Docker + Docker Compose |

---

## Integrations

### OEM Adapters
| OEM | Status | Note |
|-----|--------|------|
| Ather Energy | Stub | Requires Ather Fleet API partnership |
| OLA Electric | Stub | Requires OLA fleet API access |
| TVS | Stub | Requires TVS fleet data agreement |

Set `OEM_MODE=mock` (default) for development. Real telemetry adapters activate at `OEM_MODE=live`.

### Charging Networks
| Network | Status | Note |
|---------|--------|------|
| Chargezone | Stub | Requires B2B contract |
| Statiq | Stub | Requires B2B contract |

Set `CHARGING_NETWORK_MODE=mock` (default) for development.

---

## Quick Start

```bash
git clone https://github.com/sarathchandraboddepalli/chargemesh
cd chargemesh
cp .env.example .env    # generate JWT_SECRET_KEY and ENCRYPTION_KEY before use
docker-compose up --build
```

Run migrations:
```bash
docker-compose exec api alembic upgrade head
```

Services:
- **Fleet Dashboard:** http://localhost:3000
- **REST API:** http://localhost:8000
- **Swagger docs:** http://localhost:8000/docs (DEBUG=true only)
- **OCPP Central System:** ws://localhost:9000/ocpp/{network_id}/{station_id}
- **MQTT Broker:** mqtt://localhost:1883

### Connecting a Charge Point (OCPP)
```
ws://localhost:9000/ocpp/<network_id>/<station_uuid>
Subprotocol: ocpp1.6
```
The `station_uuid` must exist in the `charging_stations` table. Stations self-register via `BootNotification` and are marked online/offline automatically.

### Running Tests
```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

---

## Key API Endpoints

```
# Fleet management
GET  /api/v1/fleet/                    # All vehicles with status
POST /api/v1/fleet/                    # Register vehicle
GET  /api/v1/fleet/{id}                # Vehicle detail + telemetry

# Charging stations
GET  /api/v1/stations/                 # All stations with availability
GET  /api/v1/stations/{id}             # Station detail + active sessions

# Charging sessions
GET  /api/v1/sessions/                 # Session history
GET  /api/v1/sessions/{id}             # Session detail with energy data

# Batteries
GET  /api/v1/batteries/                # Battery inventory with SoH
GET  /api/v1/batteries/{id}            # Battery detail + thermal history

# Thermal
GET  /api/v1/thermal/                  # Active thermal alerts
GET  /api/v1/thermal/{battery_id}      # Battery thermal history

# Settlement
GET  /api/v1/ledger/settlements/       # Settlement reports
POST /api/v1/ledger/settlements/       # Generate settlement report

# Dispatch
GET  /api/v1/dispatch/                 # Active dispatch recommendations
POST /api/v1/dispatch/config           # Update dispatch thresholds

# Telemetry ingestion
POST /api/v1/telemetry/                # Ingest telemetry records
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | — | JWT signing key (generate with `openssl rand -hex 32`) |
| `ENCRYPTION_KEY` | Yes | — | Fernet key for token encryption at rest |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection |
| `MQTT_BROKER_URL` | No | `mqtt://localhost:1883` | MQTT broker |
| `OCPP_SERVER_PORT` | No | `9000` | OCPP WebSocket server port |
| `THERMAL_WARNING_THRESHOLD` | No | `42.0` | Warning alert threshold (°C) |
| `THERMAL_CRITICAL_THRESHOLD` | No | `48.0` | Critical alert threshold (°C) |
| `DISPATCH_SOC_THRESHOLD` | No | `25.0` | Dispatch trigger SoC (%) |
| `DISPATCH_SAFETY_BUFFER_KM` | No | `10.0` | Safety buffer for dispatch range calc |
| `OEM_MODE` | No | `mock` | `mock` or `live` |
| `CHARGING_NETWORK_MODE` | No | `mock` | `mock` or `live` |
