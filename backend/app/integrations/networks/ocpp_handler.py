"""
ChargeMesh — OCPP 1.6 Message Handler
Processes OCPP messages from charge points and updates database state.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.network import ChargingStation
from app.models.session import ChargingSession


async def handle_boot_notification(
    db: AsyncSession,
    station_id: uuid.UUID,
    charge_point_vendor: str,
    charge_point_model: str,
    charge_point_serial_number: Optional[str],
) -> dict:
    """Update station record on BootNotification."""
    result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
    station = result.scalar_one_or_none()
    if station:
        station.is_operational = True
        station.last_status_update = datetime.now(timezone.utc)
        db.add(station)
        await db.flush()
    return {
        "currentTime": datetime.now(timezone.utc).isoformat(),
        "interval": 300,
        "status": "Accepted",
    }


async def handle_heartbeat(db: AsyncSession, station_id: uuid.UUID) -> dict:
    """Update last_status_update on heartbeat."""
    result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
    station = result.scalar_one_or_none()
    if station:
        station.last_status_update = datetime.now(timezone.utc)
        station.is_operational = True
        db.add(station)
        await db.flush()
    return {"currentTime": datetime.now(timezone.utc).isoformat()}


async def handle_status_notification(
    db: AsyncSession,
    station_id: uuid.UUID,
    connector_id: int,
    status: str,
    error_code: str,
) -> dict:
    """Update connector availability from StatusNotification."""
    result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
    station = result.scalar_one_or_none()
    if station:
        if status == "Available":
            station.available_connectors = min(
                station.total_connectors,
                station.available_connectors + 1
            )
        elif status in ("Charging", "Occupied"):
            station.available_connectors = max(0, station.available_connectors - 1)
        elif status == "Faulted":
            station.is_operational = False
        station.last_status_update = datetime.now(timezone.utc)
        db.add(station)
        await db.flush()
    return {}


async def handle_start_transaction(
    db: AsyncSession,
    station_id: uuid.UUID,
    connector_id: int,
    id_tag: str,
    meter_start: int,
    timestamp: datetime,
) -> dict:
    """Authorize and record session start from StartTransaction."""
    result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
    station = result.scalar_one_or_none()

    transaction_id = int(uuid.uuid4().int >> 96)  # unique int transaction ID

    if station and station.is_operational:
        # Create or update session
        session = ChargingSession(
            station_id=station_id,
            network_id=station.network_id,
            external_session_id=str(transaction_id),
            status="active",
            started_at=timestamp,
            booked_at=timestamp,
            booking_type="manual",
            soc_at_start=None,
        )
        db.add(session)
        station.available_connectors = max(0, station.available_connectors - 1)
        db.add(station)
        await db.flush()

        return {
            "transactionId": transaction_id,
            "idTagInfo": {"status": "Accepted"},
        }

    return {
        "transactionId": transaction_id,
        "idTagInfo": {"status": "Blocked"},
    }


async def handle_stop_transaction(
    db: AsyncSession,
    station_id: uuid.UUID,
    transaction_id: int,
    id_tag: Optional[str],
    meter_stop: int,
    timestamp: datetime,
    reason: Optional[str],
) -> dict:
    """Finalize session from StopTransaction."""
    result = await db.execute(
        select(ChargingSession).where(
            ChargingSession.external_session_id == str(transaction_id),
            ChargingSession.station_id == station_id,
        )
    )
    session = result.scalar_one_or_none()
    if session:
        session.status = "completed"
        session.ended_at = timestamp
        if session.started_at:
            duration = (timestamp - session.started_at).total_seconds() / 60
            session.duration_minutes = int(duration)
        db.add(session)

        # Update station availability
        s_result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
        station = s_result.scalar_one_or_none()
        if station:
            station.available_connectors = min(station.total_connectors, station.available_connectors + 1)
            db.add(station)

        await db.flush()

    return {"idTagInfo": {"status": "Accepted"}}


async def handle_meter_values(
    db: AsyncSession,
    station_id: uuid.UUID,
    transaction_id: Optional[int],
    meter_values: list[dict],
) -> dict:
    """Process MeterValues to track energy delivered during session."""
    if not transaction_id:
        return {}

    result = await db.execute(
        select(ChargingSession).where(
            ChargingSession.external_session_id == str(transaction_id),
        )
    )
    session = result.scalar_one_or_none()
    if session:
        # Extract kWh from the latest energy.active.import.register reading
        for mv in meter_values:
            for sv in mv.get("sampledValue", []):
                if sv.get("measurand") == "Energy.Active.Import.Register":
                    try:
                        kwh = float(sv.get("value", 0)) / 1000  # Wh → kWh
                        session.energy_delivered_kwh = kwh
                        db.add(session)
                    except (ValueError, TypeError):
                        pass
        await db.flush()
    return {}
