"""
ChargeMesh — Ola Electric OEM Adapter (stub)
Real implementation requires Ola Electric API partnership.
"""

import uuid
from app.integrations.oem.base import BaseOEMAdapter, OEMTelemetryRecord


class OlaOEMAdapter(BaseOEMAdapter):
    """
    Ola Electric S1 Pro telemetry adapter.
    NOTE: Ola Electric does not publicly expose a fleet telemetry API.
    This requires a partnership agreement. Contact: fleet@olaelectric.com
    """

    @property
    def oem_slug(self) -> str:
        return "ola"

    async def test_connection(self) -> bool:
        print("[ChargeMesh] [OLA ADAPTER] test_connection() → NOT IMPLEMENTED (partnership required)")
        return False

    async def fetch_telemetry(self, vehicle_oem_ids: list[str]) -> list[OEMTelemetryRecord]:
        raise NotImplementedError(
            "Ola Electric API integration requires a signed partnership agreement. "
            "Use OEM_MODE=mock for development. "
            "Contact Ola Electric fleet team to obtain API credentials."
        )
