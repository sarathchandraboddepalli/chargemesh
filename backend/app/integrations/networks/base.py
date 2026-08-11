"""
ChargeMesh — Charging Network Client Abstract Base Class
All network clients (ChargeZone, Statiq, etc.) must implement this.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class StationStatus:
    external_station_id: str
    name: str
    latitude: float
    longitude: float
    total_connectors: int
    available_connectors: int
    is_operational: bool
    pricing_per_kwh: Optional[float]
    last_updated: datetime


@dataclass
class BookingResult:
    success: bool
    external_session_id: Optional[str]
    message: str


class BaseNetworkClient(ABC):
    """Abstract base for charging network API clients."""

    def __init__(self, network_id, config: dict):
        self.network_id = network_id
        self.config = config

    @abstractmethod
    async def get_stations(self) -> list[StationStatus]:
        """Fetch all stations from the network."""
        ...

    @abstractmethod
    async def get_station_status(self, external_station_id: str) -> Optional[StationStatus]:
        """Get real-time status of a specific station."""
        ...

    @abstractmethod
    async def book_slot(
        self,
        external_station_id: str,
        connector_id: str,
        vehicle_id: str,
        duration_minutes: int,
    ) -> BookingResult:
        """Book a charging slot. Returns booking confirmation."""
        ...

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connectivity."""
        ...
