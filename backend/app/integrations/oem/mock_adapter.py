"""
ChargeMesh — Mock OEM Adapter
Generates realistic telemetry for Ola S1 Pro, Ather 450X, TVS iQube vehicles.

Mock fleet composition:
  - 20 Ola S1 Pro: Mumbai South + North zones
  - 10 Ather 450X: Bengaluru Central zone
  - 5 TVS iQube: Pune zone

Special scenarios simulated:
  - MH02AB1234: drops to 18% SoC with 3 deliveries remaining (dispatch trigger)
  - KA01AB5678: battery spikes to 46°C during noon fast-charge (thermal alert)
  - MH02CD9012: battery swap at 2pm, 42 kWh consumed (BaaS ledger)

This adapter logs clearly that it is generating mock data — it will never
silently pretend to be a real OEM API.
"""

import math
import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.integrations.oem.base import BaseOEMAdapter, OEMTelemetryRecord

# Vehicle specifications
VEHICLE_SPECS = {
    "ola_s1_pro": {
        "battery_kwh": 3.97,
        "max_range_km": 181.0,
        "efficiency_kwh_per_km": 0.022,  # ~22 Wh/km
        "zones": ["Mumbai South", "Mumbai North"],
        "typical_temp": 38.0,
        "fast_charge_power_kw": 1.8,
        "slow_charge_power_kw": 0.75,
    },
    "ather_450x": {
        "battery_kwh": 3.7,
        "max_range_km": 146.0,
        "efficiency_kwh_per_km": 0.025,
        "zones": ["Bengaluru Central"],
        "typical_temp": 36.0,
        "fast_charge_power_kw": 2.4,
        "slow_charge_power_kw": 0.75,
    },
    "tvs_iqube": {
        "battery_kwh": 3.04,
        "max_range_km": 140.0,
        "efficiency_kwh_per_km": 0.022,
        "zones": ["Pune"],
        "typical_temp": 35.0,
        "fast_charge_power_kw": 1.5,
        "slow_charge_power_kw": 0.75,
    },
}

# Mock fleet: registration → (oem_slug, oem_vehicle_id, internal_uuid)
MOCK_FLEET: dict[str, dict] = {}


def _build_mock_fleet():
    """Initialize mock fleet composition."""
    fleet = {}
    # 20 Ola S1 Pro — Mumbai South (10) + Mumbai North (10)
    for i in range(1, 21):
        reg = f"MH02AB{1000 + i:04d}"
        fleet[reg] = {
            "oem_slug": "ola_s1_pro",
            "oem_vehicle_id": f"OLA-S1P-{i:04d}",
            "zone": "Mumbai South" if i <= 10 else "Mumbai North",
            "id": uuid.uuid4(),
        }
    # Override the critical scenario vehicle
    fleet["MH02AB1234"] = {
        "oem_slug": "ola_s1_pro",
        "oem_vehicle_id": "OLA-S1P-CRIT-001",
        "zone": "Mumbai South",
        "id": uuid.uuid4(),
        "scenario": "low_soc_critical",  # 18% SoC + 3 deliveries remaining
    }

    # 10 Ather 450X — Bengaluru Central
    for i in range(1, 11):
        reg = f"KA01AB{5000 + i:04d}"
        fleet[reg] = {
            "oem_slug": "ather_450x",
            "oem_vehicle_id": f"ATHER-450X-{i:04d}",
            "zone": "Bengaluru Central",
            "id": uuid.uuid4(),
        }
    # Override the thermal scenario vehicle
    fleet["KA01AB5678"] = {
        "oem_slug": "ather_450x",
        "oem_vehicle_id": "ATHER-450X-THERM-001",
        "zone": "Bengaluru Central",
        "id": uuid.uuid4(),
        "scenario": "thermal_spike",  # 46°C during noon fast-charge
    }

    # 5 TVS iQube — Pune
    for i in range(1, 6):
        reg = f"MH12CD{9000 + i:04d}"
        fleet[reg] = {
            "oem_slug": "tvs_iqube",
            "oem_vehicle_id": f"TVS-IQ-{i:04d}",
            "zone": "Pune",
            "id": uuid.uuid4(),
        }
    # Override the swap scenario vehicle
    fleet["MH02CD9012"] = {
        "oem_slug": "ola_s1_pro",
        "oem_vehicle_id": "OLA-S1P-SWAP-001",
        "zone": "Mumbai South",
        "id": uuid.uuid4(),
        "scenario": "battery_swap",  # 42 kWh consumed, swap at 2pm
    }

    return fleet


MOCK_FLEET = _build_mock_fleet()


def _delivery_day_soc(hour: float, scenario: Optional[str] = None) -> float:
    """
    Model a typical delivery day SoC curve:
    - 8am: 90% (start of shift, charged overnight)
    - 1pm: 25% (midday depletion from morning deliveries)
    - 2pm: 75% (after charging session at noon)
    - 6pm: 30% (end of shift)
    """
    if scenario == "low_soc_critical":
        # Vehicle stuck at 18% all afternoon (critical scenario)
        if hour >= 12:
            return max(8.0, 18.0 - (hour - 12) * 1.5)
        return max(20.0, 90.0 - hour * 6.0)

    if scenario == "battery_swap":
        # Normal decline until 2pm swap, then reset to new battery SoC
        if hour < 14:
            soc = 90.0 - hour * 4.5
            return max(15.0, soc)
        else:
            return max(20.0, 85.0 - (hour - 14) * 4.5)

    # Normal delivery day pattern
    if hour < 13:
        soc = 90.0 - (hour - 8) * 13.0  # 90% at 8am → 25% at 1pm
    elif hour < 14:
        soc = 25.0 + (hour - 13) * 50.0  # charging: 25% → 75%
    else:
        soc = 75.0 - (hour - 14) * 11.25  # 75% at 2pm → 30% at 6pm
    return max(5.0, min(100.0, soc + random.uniform(-3, 3)))


def _battery_temp(hour: float, is_charging: bool, scenario: Optional[str]) -> float:
    """
    Model battery temperature during a delivery day.
    Peaks around noon (ambient heat + operation).
    """
    base_ambient = 32.0 + 8.0 * math.sin(math.pi * (hour - 6) / 12)  # peaks at noon ~40°C
    thermal_offset = 5.0  # battery runs hotter than ambient

    if scenario == "thermal_spike" and 11 <= hour <= 14 and is_charging:
        # Thermal spike: 46°C during noon fast-charge
        return 44.0 + random.uniform(0, 4.0)  # 44-48°C range

    if is_charging:
        return base_ambient + thermal_offset + random.uniform(2.0, 6.0)
    return base_ambient + thermal_offset + random.uniform(-2.0, 2.0)


# Mumbai South station coordinates (for telemetry location data)
ZONE_COORDS = {
    "Mumbai South": (18.9220, 72.8347),
    "Mumbai North": (19.1136, 72.8697),
    "Bengaluru Central": (12.9716, 77.5946),
    "Pune": (18.5204, 73.8567),
}


class MockOEMAdapter(BaseOEMAdapter):
    """
    Mock OEM adapter for development and testing.
    Generates realistic telemetry for the mock fleet.
    IMPORTANT: This adapter logs that it is generating mock data.
    """

    @property
    def oem_slug(self) -> str:
        return "mock"

    async def test_connection(self) -> bool:
        print("[ChargeMesh] [MOCK OEM] test_connection() → True (mock adapter)")
        return True

    async def fetch_telemetry(
        self,
        vehicle_oem_ids: list[str],
    ) -> list[OEMTelemetryRecord]:
        """
        Generate realistic telemetry records for the mock fleet.
        Logs clearly that this is mock data.
        """
        now = datetime.now(timezone.utc)
        hour = now.hour + now.minute / 60.0  # fractional hour in UTC (approx IST = UTC+5:30)
        ist_hour = (hour + 5.5) % 24  # convert to IST

        records = []
        # Generate for all known mock vehicles (not just requested OEM IDs for MVP)
        for reg, vehicle_info in MOCK_FLEET.items():
            oem_slug = vehicle_info["oem_slug"]
            spec = VEHICLE_SPECS.get(oem_slug, VEHICLE_SPECS["ola_s1_pro"])
            scenario = vehicle_info.get("scenario")
            zone = vehicle_info.get("zone", "Mumbai South")
            base_lat, base_lng = ZONE_COORDS.get(zone, (18.9220, 72.8347))

            soc = _delivery_day_soc(ist_hour, scenario)
            is_charging = (scenario != "low_soc_critical" and 13 <= ist_hour <= 14)
            battery_temp = _battery_temp(ist_hour, is_charging, scenario)

            estimated_range = (soc / 100.0) * spec["max_range_km"] * (0.9 + random.uniform(-0.05, 0.05))
            speed = 0.0 if is_charging else random.uniform(15.0, 35.0)
            charging_power = spec["fast_charge_power_kw"] if is_charging else None

            # Small random location jitter within zone
            lat = base_lat + random.uniform(-0.05, 0.05)
            lng = base_lng + random.uniform(-0.05, 0.05)

            record = OEMTelemetryRecord(
                vehicle_id=vehicle_info["id"],
                oem_vehicle_id=vehicle_info["oem_vehicle_id"],
                recorded_at=now,
                state_of_charge=round(soc, 2),
                state_of_health=round(random.uniform(88.0, 99.0), 2),
                latitude=round(lat, 7),
                longitude=round(lng, 7),
                speed_kmh=round(speed, 1),
                battery_temp_celsius=round(battery_temp, 1),
                ambient_temp_celsius=round(battery_temp - 5.0, 1),
                odometer_km=round(random.uniform(1000, 50000), 1),
                is_charging=is_charging,
                charging_power_kw=charging_power,
                estimated_range_km=round(estimated_range, 1),
                battery_id=f"BAT-{vehicle_info['oem_vehicle_id']}",
                raw_data={
                    "oem": oem_slug,
                    "reg": reg,
                    "zone": zone,
                    "scenario": scenario,
                    "mock": True,
                },
            )
            records.append(record)

        print(
            f"[ChargeMesh] [MOCK OEM] Generated {len(records)} telemetry records "
            f"(IST hour={ist_hour:.1f}). THIS IS MOCK DATA — NOT REAL OEM TELEMETRY."
        )
        return records
