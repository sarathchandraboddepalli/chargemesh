"""
ChargeMesh — Mock Charging Network Client
Simulates ChargeZone (OCPP) and Statiq (proprietary) networks.

Mock data:
  ChargeZone Network (OCPP):
    - 3 stations in Mumbai South, 2 connectors each
    - Station #2 has 1 connector offline (simulates real-world partial outages)
    - Pricing: Rs.10/kWh

  Statiq Network (proprietary):
    - 2 stations in Bengaluru, all operational
    - Pricing: Rs.12/kWh

This client logs clearly that it is returning mock data.
"""

import random
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.integrations.networks.base import BaseNetworkClient, BookingResult, StationStatus

CHARGEZONE_STATIONS = [
    StationStatus(
        external_station_id="CZ-MUM-001",
        name="ChargeZone Byculla",
        latitude=18.9785,
        longitude=72.8353,
        total_connectors=2,
        available_connectors=2,
        is_operational=True,
        pricing_per_kwh=10.0,
        last_updated=datetime.now(timezone.utc),
    ),
    StationStatus(
        external_station_id="CZ-MUM-002",
        name="ChargeZone Worli",
        latitude=18.9980,
        longitude=72.8166,
        total_connectors=2,
        available_connectors=1,  # 1 connector offline (mock outage)
        is_operational=True,      # station operational but not at full capacity
        pricing_per_kwh=10.0,
        last_updated=datetime.now(timezone.utc),
    ),
    StationStatus(
        external_station_id="CZ-MUM-003",
        name="ChargeZone Dadar",
        latitude=19.0176,
        longitude=72.8450,
        total_connectors=2,
        available_connectors=2,
        is_operational=True,
        pricing_per_kwh=10.0,
        last_updated=datetime.now(timezone.utc),
    ),
]

STATIQ_STATIONS = [
    StationStatus(
        external_station_id="STQ-BLR-001",
        name="Statiq Indiranagar",
        latitude=12.9784,
        longitude=77.6408,
        total_connectors=3,
        available_connectors=3,
        is_operational=True,
        pricing_per_kwh=12.0,
        last_updated=datetime.now(timezone.utc),
    ),
    StationStatus(
        external_station_id="STQ-BLR-002",
        name="Statiq Koramangala",
        latitude=12.9352,
        longitude=77.6245,
        total_connectors=2,
        available_connectors=2,
        is_operational=True,
        pricing_per_kwh=12.0,
        last_updated=datetime.now(timezone.utc),
    ),
]


class MockNetworkClient(BaseNetworkClient):
    """Mock charging network client for ChargeZone and Statiq."""

    def __init__(self, network_id, config: dict):
        super().__init__(network_id, config)
        self.network_slug = config.get("network_slug", "chargezone")

    async def test_connection(self) -> bool:
        print(f"[ChargeMesh] [MOCK NETWORK] test_connection() → True ({self.network_slug}). THIS IS MOCK DATA.")
        return True

    async def get_stations(self) -> list[StationStatus]:
        if self.network_slug == "statiq":
            stations = STATIQ_STATIONS
        else:
            stations = CHARGEZONE_STATIONS

        # Update timestamps
        for s in stations:
            s.last_updated = datetime.now(timezone.utc)

        print(
            f"[ChargeMesh] [MOCK NETWORK] get_stations() → {len(stations)} stations "
            f"({self.network_slug}). THIS IS MOCK DATA."
        )
        return stations

    async def get_station_status(self, external_station_id: str) -> Optional[StationStatus]:
        all_stations = CHARGEZONE_STATIONS + STATIQ_STATIONS
        for s in all_stations:
            if s.external_station_id == external_station_id:
                s.last_updated = datetime.now(timezone.utc)
                return s
        return None

    async def book_slot(
        self,
        external_station_id: str,
        connector_id: str,
        vehicle_id: str,
        duration_minutes: int = 60,
    ) -> BookingResult:
        """
        Mock booking: always succeeds if station is available.
        Logs what the real API call would do.
        """
        station = await self.get_station_status(external_station_id)
        if not station or not station.is_operational or station.available_connectors == 0:
            print(
                f"[ChargeMesh] [MOCK NETWORK] book_slot() → FAILED "
                f"(station {external_station_id} not available)"
            )
            return BookingResult(success=False, external_session_id=None, message="Station not available")

        session_id = f"MOCK-{self.network_slug.upper()}-{uuid.uuid4().hex[:8].upper()}"
        print(
            f"[ChargeMesh] [MOCK NETWORK] book_slot() → SUCCESS "
            f"station={external_station_id} vehicle={vehicle_id} "
            f"session={session_id} duration={duration_minutes}min. THIS IS MOCK DATA."
        )
        return BookingResult(
            success=True,
            external_session_id=session_id,
            message=f"Slot booked successfully at {station.name}",
        )
