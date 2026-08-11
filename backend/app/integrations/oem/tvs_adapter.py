"""ChargeMesh — TVS iQube OEM Adapter (stub)"""

from app.integrations.oem.base import BaseOEMAdapter, OEMTelemetryRecord


class TVSOEMAdapter(BaseOEMAdapter):
    """TVS iQube telemetry adapter. Requires TVS Motor fleet API partnership."""

    @property
    def oem_slug(self) -> str:
        return "tvs"

    async def test_connection(self) -> bool:
        print("[ChargeMesh] [TVS ADAPTER] NOT IMPLEMENTED (partnership required)")
        return False

    async def fetch_telemetry(self, vehicle_oem_ids: list[str]) -> list[OEMTelemetryRecord]:
        raise NotImplementedError(
            "TVS Motor API integration requires a signed partnership agreement. "
            "Use OEM_MODE=mock for development."
        )
