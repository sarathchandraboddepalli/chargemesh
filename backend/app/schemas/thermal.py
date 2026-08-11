"""ChargeMesh — Thermal Alert Schemas (Pydantic v2)"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ThermalAlertOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    battery_id: uuid.UUID
    vehicle_id: uuid.UUID | None
    alert_type: str
    severity: str
    temperature_celsius: Decimal | None
    threshold_celsius: Decimal | None
    message: str | None
    is_resolved: bool
    resolved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ThermalThresholdUpdate(BaseModel):
    warning_celsius: float | None = None
    critical_celsius: float | None = None


class BatteryThermalHistory(BaseModel):
    battery_id: uuid.UUID
    accumulated_stress: float
    stress_score_label: str  # "low", "moderate", "high", "critical"
    peak_temp_celsius: float | None
    alerts: list[ThermalAlertOut]
