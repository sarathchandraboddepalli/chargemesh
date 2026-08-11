"""
ChargeMesh — OEM Adapter Abstract Base Class
All OEM adapters must implement this interface.
Switchable via OEM_MODE environment variable.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OEMTelemetryRecord:
    """Normalized telemetry record from any OEM."""
    vehicle_id: uuid.UUID
    oem_vehicle_id: str
    recorded_at: datetime
    state_of_charge: Optional[float]          # 0-100%
    state_of_health: Optional[float]          # 0-100%
    latitude: Optional[float]
    longitude: Optional[float]
    speed_kmh: Optional[float]
    battery_temp_celsius: Optional[float]
    ambient_temp_celsius: Optional[float]
    odometer_km: Optional[float]
    is_charging: bool
    charging_power_kw: Optional[float]
    estimated_range_km: Optional[float]
    battery_id: Optional[str]                 # OEM-reported battery serial
    raw_data: Optional[dict]


class BaseOEMAdapter(ABC):
    """
    Abstract base class for OEM telemetry adapters.

    Each OEM (Ola Electric, Ather, TVS, Bajaj, Hero) requires a concrete
    implementation that handles their specific API format.

    Implementations must handle:
    - Authentication (OAuth, API key, certificate)
    - Rate limiting (OEM APIs may throttle)
    - Data normalization to OEMTelemetryRecord
    - Error handling and reconnection
    """

    def __init__(self, adapter_id: uuid.UUID, config: dict):
        self.adapter_id = adapter_id
        self.config = config

    @abstractmethod
    async def fetch_telemetry(
        self,
        vehicle_oem_ids: list[str],
    ) -> list[OEMTelemetryRecord]:
        """
        Fetch telemetry for the given OEM vehicle IDs.
        Returns normalized telemetry records.
        """
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connectivity to the OEM API. Returns True if healthy."""
        ...

    @property
    @abstractmethod
    def oem_slug(self) -> str:
        """Short identifier: 'ola', 'ather', 'tvs', 'bajaj', 'hero'"""
        ...
