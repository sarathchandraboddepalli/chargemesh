"""OEM Adapter factory — selects adapter based on OEM_MODE and oem_slug."""

import uuid
from app.config import settings
from app.integrations.oem.base import BaseOEMAdapter


def get_oem_adapter(oem_slug: str, adapter_id: uuid.UUID, config: dict) -> BaseOEMAdapter:
    """Factory: returns the appropriate OEM adapter based on config."""
    if settings.OEM_MODE == "mock":
        from app.integrations.oem.mock_adapter import MockOEMAdapter
        return MockOEMAdapter(adapter_id=adapter_id, config=config)

    adapters = {
        "ola": "app.integrations.oem.ola_adapter.OlaOEMAdapter",
        "ather": "app.integrations.oem.ather_adapter.AtherOEMAdapter",
        "tvs": "app.integrations.oem.tvs_adapter.TVSOEMAdapter",
    }
    if oem_slug not in adapters:
        raise ValueError(f"Unknown OEM slug: {oem_slug}. Supported: {list(adapters.keys())}")

    import importlib
    module_path, class_name = adapters[oem_slug].rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls(adapter_id=adapter_id, config=config)
