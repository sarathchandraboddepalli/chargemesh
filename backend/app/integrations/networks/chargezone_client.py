"""ChargeMesh — ChargeZone Network Client (stub — requires API partnership)"""

from app.integrations.networks.base import BaseNetworkClient, BookingResult, StationStatus


class ChargeZoneClient(BaseNetworkClient):
    """ChargeZone OCPP network client. Requires ChargeZone API partnership."""

    async def test_connection(self) -> bool:
        print("[ChargeMesh] [CHARGEZONE] NOT IMPLEMENTED — Use CHARGING_NETWORK_MODE=mock for development")
        return False

    async def get_stations(self) -> list[StationStatus]:
        raise NotImplementedError("ChargeZone API requires signed partnership. Use mock mode.")

    async def get_station_status(self, external_station_id: str):
        raise NotImplementedError("ChargeZone API requires signed partnership. Use mock mode.")

    async def book_slot(self, external_station_id, connector_id, vehicle_id, duration_minutes=60):
        raise NotImplementedError("ChargeZone API requires signed partnership. Use mock mode.")
