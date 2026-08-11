"""Network client factory."""

from app.config import settings
from app.integrations.networks.base import BaseNetworkClient


def get_network_client(network_slug: str, network_id, config: dict) -> BaseNetworkClient:
    if settings.CHARGING_NETWORK_MODE == "mock":
        from app.integrations.networks.mock_network import MockNetworkClient
        return MockNetworkClient(network_id=network_id, config={**config, "network_slug": network_slug})

    clients = {"chargezone": "chargezone_client.ChargeZoneClient", "statiq": "statiq_client.StatiqClient"}
    if network_slug not in clients:
        raise ValueError(f"Unknown network slug: {network_slug}")
    module_name, class_name = clients[network_slug].rsplit(".", 1)
    import importlib
    module = importlib.import_module(f"app.integrations.networks.{module_name}")
    cls = getattr(module, class_name)
    return cls(network_id=network_id, config=config)
