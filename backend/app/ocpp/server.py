"""
ChargeMesh — OCPP 1.6 WebSocket Central System Server
Runs as a separate Docker container on port 9000.

Charging stations connect via:
  wss://api.chargemesh.in/ocpp/{network_id}/{station_id}

The station_id must match a charging_stations record in the database.
Heartbeat timeout: 3 minutes without heartbeat → station marked offline.

Usage:
  python -m app.ocpp.server
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

import websockets
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.network import ChargingStation
from app.ocpp.charge_point import ChargeMeshChargePoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [OCPP] %(message)s")
logger = logging.getLogger(__name__)

# Track connected charge points for heartbeat monitoring
CONNECTED_CHARGE_POINTS: dict[str, tuple[ChargeMeshChargePoint, datetime]] = {}
HEARTBEAT_TIMEOUT_SECONDS = 180  # 3 minutes


async def on_connect(websocket, path: str):
    """
    Handle a new WebSocket connection from a charging station.

    Path format: /ocpp/{network_id}/{station_id}
    The station_id is used to look up the charging_stations record.
    """
    logger.info(f"New connection from {websocket.remote_address} path={path}")

    # Parse path to extract station_id
    parts = path.strip("/").split("/")
    if len(parts) < 3 or parts[0] != "ocpp":
        await websocket.close(code=4001, reason="Invalid OCPP URL path. Expected: /ocpp/{network_id}/{station_id}")
        return

    try:
        station_id = uuid.UUID(parts[2])
    except ValueError:
        await websocket.close(code=4002, reason="Invalid station_id format (must be UUID)")
        return

    # Verify station exists in database
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
        station = result.scalar_one_or_none()
        if not station:
            await websocket.close(code=4003, reason=f"Station {station_id} not found in ChargeMesh")
            return
        charge_point_id = f"{station.external_station_id}"

    logger.info(f"Charging station authenticated: {charge_point_id} (station_id={station_id})")

    # Create ChargePoint handler
    charge_point = ChargeMeshChargePoint(
        id=charge_point_id,
        connection=websocket,
        station_id=station_id,
    )
    CONNECTED_CHARGE_POINTS[charge_point_id] = (charge_point, datetime.now(timezone.utc))

    try:
        await charge_point.start()
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed: {charge_point_id}")
    finally:
        CONNECTED_CHARGE_POINTS.pop(charge_point_id, None)

        # Mark station as offline when disconnected
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
            station = result.scalar_one_or_none()
            if station:
                station.is_operational = False
                station.last_status_update = datetime.now(timezone.utc)
                db.add(station)
                await db.commit()
        logger.info(f"Marked station {station_id} as offline")


async def heartbeat_monitor():
    """
    Monitor connected charge points for heartbeat timeout.
    If a charge point stops sending heartbeats for > 3 minutes,
    mark its station as offline in the database.
    """
    while True:
        await asyncio.sleep(60)  # check every minute
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS)
        for cp_id, (cp, last_seen) in list(CONNECTED_CHARGE_POINTS.items()):
            if last_seen < cutoff:
                logger.warning(
                    f"Heartbeat timeout for {cp_id} (last seen: {last_seen.isoformat()}). "
                    f"Marking station offline."
                )
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(ChargingStation).where(ChargingStation.id == cp.station_id)
                    )
                    station = result.scalar_one_or_none()
                    if station:
                        station.is_operational = False
                        station.last_status_update = datetime.now(timezone.utc)
                        db.add(station)
                        await db.commit()


async def main():
    """Start the OCPP WebSocket server."""
    host = settings.OCPP_SERVER_HOST
    port = settings.OCPP_SERVER_PORT

    logger.info(f"Starting ChargeMesh OCPP 1.6 Central System on {host}:{port}")
    logger.info("Charging stations should connect to: ws://<host>:{port}/ocpp/<network_id>/<station_id>")

    # Start heartbeat monitor in background
    asyncio.create_task(heartbeat_monitor())

    server = await websockets.serve(
        on_connect,
        host,
        port,
        subprotocols=["ocpp1.6"],
        ping_interval=20,
        ping_timeout=20,
    )
    logger.info(f"OCPP Central System ready on ws://{host}:{port}")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
