"""ChargeMesh — Ather Energy OEM Adapter (stub)"""

from app.integrations.oem.base import BaseOEMAdapter, OEMTelemetryRecord


class AtherOEMAdapter(BaseOEMAdapter):
    """Ather 450X telemetry adapter. Requires Ather fleet API partnership."""

    @property
    def oem_slug(self) -> str:
        return "ather"

    async def test_connection(self) -> bool:
        print("[ChargeMesh] [ATHER ADAPTER] NOT IMPLEMENTED (partnership required)")
        return False

    async def fetch_telemetry(self, vehicle_oem_ids: list[str]) -> list[OEMTelemetryRecord]:
        raise NotImplementedError(
            "Ather Energy API integration requires a signed partnership agreement. "
            "Use OEM_MODE=mock for development."
        )
