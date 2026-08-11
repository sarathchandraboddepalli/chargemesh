"""ChargeMesh — Statiq Network Client (stub — requires API partnership)"""

from app.integrations.networks.base import BaseNetworkClient, BookingResult, StationStatus


class StatiqClient(BaseNetworkClient):
    """Statiq proprietary API client. Requires Statiq API partnership."""

    async def test_connection(self) -> bool:
        print("[ChargeMesh] [STATIQ] NOT IMPLEMENTED — Use CHARGING_NETWORK_MODE=mock for development")
        return False

    async def get_stations(self) -> list[StationStatus]:
        raise NotImplementedError("Statiq API requires signed partnership. Use mock mode.")

    async def get_station_status(self, external_station_id: str):
        raise NotImplementedError("Statiq API requires signed partnership. Use mock mode.")

    async def book_slot(self, external_station_id, connector_id, vehicle_id, duration_minutes=60):
        raise NotImplementedError("Statiq API requires signed partnership. Use mock mode.")
