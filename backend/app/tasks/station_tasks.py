"""ChargeMesh — Station Sync Celery Tasks"""

import asyncio
import uuid
from datetime import datetime, timezone

from app.worker import celery_app


@celery_app.task(name="app.tasks.station_tasks.sync_all_station_availability", queue="telemetry")
def sync_all_station_availability():
    """Sync availability from all active charging networks every 5 minutes."""
    asyncio.run(_sync_all())


@celery_app.task(name="app.tasks.station_tasks.sync_network_stations", queue="telemetry")
def sync_network_stations(network_id_str: str):
    """Sync stations for a specific network (triggered manually or on demand)."""
    asyncio.run(_sync_network(uuid.UUID(network_id_str)))


async def _sync_all():
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.network import ChargingNetwork

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ChargingNetwork).where(ChargingNetwork.is_active == True))
        networks = result.scalars().all()

    for network in networks:
        await _sync_network(network.id)


async def _sync_network(network_id: uuid.UUID):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.network import ChargingNetwork, ChargingStation
    from app.integrations.networks import get_network_client

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ChargingNetwork).where(ChargingNetwork.id == network_id))
        network = result.scalar_one_or_none()
        if not network:
            return

        try:
            client = get_network_client(
                network_slug=network.network_slug,
                network_id=network.id,
                config={"auth_token": network.auth_token},
            )
            stations = await client.get_stations()

            now = datetime.now(timezone.utc)
            for station_data in stations:
                # Upsert station record
                existing = await db.execute(
                    select(ChargingStation).where(
                        ChargingStation.network_id == network_id,
                        ChargingStation.external_station_id == station_data.external_station_id,
                    )
                )
                station = existing.scalar_one_or_none()
                if station:
                    station.available_connectors = station_data.available_connectors
                    station.is_operational = station_data.is_operational
                    station.last_status_update = now
                    db.add(station)
                else:
                    db.add(ChargingStation(
                        network_id=network_id,
                        external_station_id=station_data.external_station_id,
                        name=station_data.name,
                        latitude=station_data.latitude,
                        longitude=station_data.longitude,
                        total_connectors=station_data.total_connectors,
                        available_connectors=station_data.available_connectors,
                        is_operational=station_data.is_operational,
                        pricing_per_kwh=station_data.pricing_per_kwh,
                        last_status_update=now,
                    ))

            network.last_heartbeat_at = now
            network.connection_status = "connected"
            network.station_count = len(stations)
            db.add(network)
            await db.commit()
            print(f"[ChargeMesh] [STATION TASK] Synced {len(stations)} stations for {network.name}")

        except Exception as e:
            print(f"[ChargeMesh] [STATION TASK] Sync failed for {network.name}: {e}")
            network.connection_status = "error"
            db.add(network)
            await db.commit()
