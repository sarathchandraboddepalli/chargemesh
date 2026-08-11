"""ChargeMesh — Vehicle Schemas (Pydantic v2)"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=4, max_length=20)
    chassis_number: str | None = None
    oem_vehicle_id: str | None = None
    model_name: str | None = None
    battery_capacity_kwh: Decimal | None = None
    max_range_km: Decimal | None = None
    zone: str | None = None
    oem_adapter_id: uuid.UUID | None = None

    model_config = {"str_strip_whitespace": True}


class VehicleUpdate(BaseModel):
    zone: str | None = None
    current_driver_id: uuid.UUID | None = None
    status: str | None = None
    model_name: str | None = None


class VehicleOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    registration_number: str
    chassis_number: str | None
    oem_vehicle_id: str | None
    model_name: str | None
    battery_capacity_kwh: Decimal | None
    max_range_km: Decimal | None
    zone: str | None
    current_driver_id: uuid.UUID | None
    current_battery_id: uuid.UUID | None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VehicleWithSoC(VehicleOut):
    """Vehicle with latest telemetry data for fleet list view."""
    current_soc: float | None = None
    current_latitude: float | None = None
    current_longitude: float | None = None
    last_telemetry_at: datetime | None = None
    estimated_range_km: float | None = None
    is_stale: bool = False  # True if last telemetry > 10 minutes ago
    driver_name: str | None = None


class VehicleBulkImportRow(BaseModel):
    registration_number: str
    model_name: str | None = None
    zone: str | None = None
    battery_capacity_kwh: float | None = None
    max_range_km: float | None = None


class FleetSummary(BaseModel):
    total_vehicles: int
    active_vehicles: int
    charging_vehicles: int
    at_risk_vehicles: int  # SoC < dispatch threshold
    soc_distribution: dict[str, int]  # {"0-20": 5, "20-40": 12, ...}
    vehicles_with_recommendations: int
    active_sessions: int
