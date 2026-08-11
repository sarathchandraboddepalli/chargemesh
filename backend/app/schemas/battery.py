"""ChargeMesh — Battery and Swap Schemas (Pydantic v2)"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class BatteryCreate(BaseModel):
    external_battery_id: str | None = None
    model: str | None = None
    nominal_capacity_kwh: Decimal | None = None
    manufacture_date: date | None = None
    current_soh: Decimal | None = None


class BatteryOut(BaseModel):
    id: uuid.UUID
    owner_org_id: uuid.UUID
    external_battery_id: str | None
    model: str | None
    nominal_capacity_kwh: Decimal | None
    manufacture_date: date | None
    current_soh: Decimal | None
    cycle_count: int
    total_kwh_delivered: Decimal
    accumulated_thermal_stress: Decimal
    current_vehicle_id: uuid.UUID | None
    status: str
    is_flagged: bool
    flag_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SwapCreate(BaseModel):
    vehicle_id: uuid.UUID
    removed_battery_id: uuid.UUID | None = None
    installed_battery_id: uuid.UUID | None = None
    baas_vendor_org_id: uuid.UUID | None = None
    swap_station_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    removed_battery_soc: float | None = None
    removed_battery_temp: float | None = None
    installed_battery_soc: float | None = None


class SwapOut(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID | None
    removed_battery_id: uuid.UUID | None
    installed_battery_id: uuid.UUID | None
    baas_vendor_org_id: uuid.UUID | None
    swap_station_name: str | None
    removed_battery_soc: Decimal | None
    removed_battery_soh: Decimal | None
    removed_battery_temp: Decimal | None
    installed_battery_soc: Decimal | None
    installed_battery_soh: Decimal | None
    kwh_consumed_this_session: Decimal | None
    degradation_this_session: Decimal | None
    settlement_amount_inr: Decimal | None
    settlement_status: str
    swapped_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
