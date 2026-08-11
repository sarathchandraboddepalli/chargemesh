"""ChargeMesh — Dispatch Schemas (Pydantic v2)"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class DispatchRecommendationOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    vehicle_id: uuid.UUID
    recommended_station_id: uuid.UUID | None
    trigger_soc: Decimal | None
    predicted_depletion_at: datetime | None
    recommended_at: datetime
    was_acted_upon: bool | None
    override_reason: str | None

    # Enriched fields
    vehicle_registration: str | None = None
    station_name: str | None = None
    station_distance_km: float | None = None

    model_config = {"from_attributes": True}


class DispatchConfigOut(BaseModel):
    soc_threshold: float
    safety_buffer_km: float


class DispatchConfigUpdate(BaseModel):
    soc_threshold: float | None = None
    safety_buffer_km: float | None = None


class DispatchOverride(BaseModel):
    reason: str
