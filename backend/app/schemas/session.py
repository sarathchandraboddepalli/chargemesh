"""ChargeMesh — Charging Session Schemas (Pydantic v2)"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SessionBookRequest(BaseModel):
    vehicle_id: uuid.UUID
    station_id: uuid.UUID
    booking_type: str = "manual"


class SessionOut(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID | None
    station_id: uuid.UUID | None
    network_id: uuid.UUID | None
    external_session_id: str | None
    status: str
    booking_type: str
    soc_at_start: Decimal | None
    soc_at_end: Decimal | None
    energy_delivered_kwh: Decimal | None
    duration_minutes: int | None
    cost_inr: Decimal | None
    battery_temp_at_start: Decimal | None
    battery_temp_max: Decimal | None
    battery_temp_at_end: Decimal | None
    booked_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
