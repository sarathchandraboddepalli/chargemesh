"""ChargeMesh — Station and Network Schemas (Pydantic v2)"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ChargingNetworkCreate(BaseModel):
    name: str
    network_slug: str
    integration_type: str  # ocpp_1_6, ocpp_2_0, proprietary
    api_base_url: str | None = None
    auth_token: str | None = None

    model_config = {"str_strip_whitespace": True}


class ChargingNetworkOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    network_slug: str
    integration_type: str
    connection_status: str
    last_heartbeat_at: datetime | None
    station_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChargingStationOut(BaseModel):
    id: uuid.UUID
    network_id: uuid.UUID
    external_station_id: str
    name: str | None
    address: str | None
    city: str | None
    state: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    total_connectors: int
    available_connectors: int
    connector_types: list[str] | None
    max_power_kw: Decimal | None
    pricing_per_kwh: Decimal | None
    is_operational: bool
    last_status_update: datetime | None
    network_name: str | None = None  # joined field

    model_config = {"from_attributes": True}


class NearbyStationQuery(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_km: float = Field(default=10.0, ge=0.1, le=100.0)
    available_only: bool = True
