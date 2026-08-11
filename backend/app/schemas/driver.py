"""ChargeMesh — Driver Schemas (Pydantic v2)"""

import uuid
from datetime import datetime, time

from pydantic import BaseModel, Field


class DriverCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    license_number: str | None = None
    assigned_vehicle_id: uuid.UUID | None = None
    shift_start: time | None = None
    shift_end: time | None = None

    model_config = {"str_strip_whitespace": True}


class DriverUpdate(BaseModel):
    name: str | None = None
    license_number: str | None = None
    assigned_vehicle_id: uuid.UUID | None = None
    shift_start: time | None = None
    shift_end: time | None = None
    is_active: bool | None = None


class DriverOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID | None
    name: str
    phone: str
    license_number: str | None
    assigned_vehicle_id: uuid.UUID | None
    shift_start: time | None
    shift_end: time | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
