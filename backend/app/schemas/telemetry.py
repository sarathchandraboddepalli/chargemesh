"""ChargeMesh — Telemetry Schemas (Pydantic v2)"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TelemetryRecord(BaseModel):
    """Single telemetry record from an OEM adapter."""
    vehicle_id: uuid.UUID
    recorded_at: datetime
    state_of_charge: float | None = Field(None, ge=0, le=100)
    state_of_health: float | None = Field(None, ge=0, le=100)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    speed_kmh: float | None = Field(None, ge=0)
    battery_temp_celsius: float | None = None
    ambient_temp_celsius: float | None = None
    odometer_km: float | None = None
    is_charging: bool = False
    charging_power_kw: float | None = None
    estimated_range_km: float | None = None
    battery_id: uuid.UUID | None = None
    raw_data: dict | None = None


class TelemetryBatchIngest(BaseModel):
    """Batch telemetry ingest from OEM adapter (API key authenticated)."""
    oem_adapter_id: uuid.UUID
    records: list[TelemetryRecord] = Field(min_length=1, max_length=1000)


class TelemetryOut(BaseModel):
    vehicle_id: uuid.UUID
    recorded_at: datetime
    state_of_charge: float | None
    state_of_health: float | None
    latitude: float | None
    longitude: float | None
    speed_kmh: float | None
    battery_temp_celsius: float | None
    ambient_temp_celsius: float | None
    odometer_km: float | None
    is_charging: bool
    charging_power_kw: float | None
    estimated_range_km: float | None
    battery_id: uuid.UUID | None

    model_config = {"from_attributes": True}
