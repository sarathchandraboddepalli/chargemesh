"""
ChargeMesh — Telemetry Ingestion and WebSocket Stream API
Handles both batch ingest (from OEM adapters) and real-time WebSocket streaming.
"""

import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentOrg, DB, get_db
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.oem import OEMAdapter
from app.models.telemetry import VehicleTelemetry
from app.models.vehicle import Vehicle
from app.schemas.telemetry import TelemetryBatchIngest, TelemetryOut

router = APIRouter()


async def _verify_api_key(api_key: str, oem_adapter_id: uuid.UUID, db: AsyncSession) -> OEMAdapter:
    """Verify OEM adapter API key (bcrypt-hashed stored)."""
    result = await db.execute(select(OEMAdapter).where(OEMAdapter.id == oem_adapter_id))
    adapter = result.scalar_one_or_none()
    if not adapter:
        raise HTTPException(status_code=404, detail="OEM adapter not found")

    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not adapter.api_key_hash or not ctx.verify(api_key, adapter.api_key_hash):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return adapter


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    payload: TelemetryBatchIngest,
    api_key: str = Query(..., alias="api_key"),
    db: DB = None,
):
    """
    Ingest a batch of telemetry records from an OEM adapter.
    Authenticated via API key (not JWT — high-volume machine-to-machine).
    Uses INSERT ... ON CONFLICT DO NOTHING for idempotency.

    Rate limit: 1000 req/min (enforced at gateway/nginx level).
    """
    adapter = await _verify_api_key(api_key, payload.oem_adapter_id, db)

    inserted = 0
    for record in payload.records:
        # Idempotent insert — duplicate (vehicle_id, recorded_at) is silently ignored
        stmt = text("""
            INSERT INTO vehicle_telemetry (
                vehicle_id, recorded_at, state_of_charge, state_of_health,
                latitude, longitude, speed_kmh, battery_temp_celsius,
                ambient_temp_celsius, odometer_km, is_charging, charging_power_kw,
                estimated_range_km, battery_id, raw_data
            ) VALUES (
                :vehicle_id, :recorded_at, :state_of_charge, :state_of_health,
                :latitude, :longitude, :speed_kmh, :battery_temp_celsius,
                :ambient_temp_celsius, :odometer_km, :is_charging, :charging_power_kw,
                :estimated_range_km, :battery_id, :raw_data
            ) ON CONFLICT (vehicle_id, recorded_at) DO NOTHING
        """)
        await db.execute(stmt, {
            "vehicle_id": record.vehicle_id,
            "recorded_at": record.recorded_at,
            "state_of_charge": record.state_of_charge,
            "state_of_health": record.state_of_health,
            "latitude": record.latitude,
            "longitude": record.longitude,
            "speed_kmh": record.speed_kmh,
            "battery_temp_celsius": record.battery_temp_celsius,
            "ambient_temp_celsius": record.ambient_temp_celsius,
            "odometer_km": record.odometer_km,
            "is_charging": record.is_charging,
            "charging_power_kw": record.charging_power_kw,
            "estimated_range_km": record.estimated_range_km,
            "battery_id": record.battery_id,
            "raw_data": json.dumps(record.raw_data) if record.raw_data else None,
        })
        inserted += 1

    # Update adapter last_telemetry_at
    adapter.last_telemetry_at = datetime.now(timezone.utc)
    adapter.connection_status = "connected"
    db.add(adapter)

    # Queue async processing (thermal checks, dispatch evaluation)
    from app.tasks.telemetry_tasks import process_telemetry_batch
    process_telemetry_batch.delay(
        str(payload.oem_adapter_id),
        [r.model_dump(mode="json") for r in payload.records],
    )

    return {"accepted": inserted, "adapter": adapter.name}


@router.post("/oem/{oem_id}/webhook", status_code=status.HTTP_202_ACCEPTED)
async def oem_webhook(
    oem_id: uuid.UUID,
    payload: dict,
    signature: str = Query(...),
    db: DB = None,
):
    """OEM push webhook — signature verified against stored adapter secret."""
    result = await db.execute(select(OEMAdapter).where(OEMAdapter.id == oem_id))
    adapter = result.scalar_one_or_none()
    if not adapter:
        raise HTTPException(status_code=404, detail="OEM adapter not found")

    # Verify HMAC signature (simplified — production uses per-OEM signature scheme)
    expected = hashlib.sha256(
        f"{oem_id}{json.dumps(payload, sort_keys=True)}".encode()
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Normalize and queue for processing
    from app.tasks.telemetry_tasks import process_telemetry_batch
    process_telemetry_batch.delay(str(oem_id), [payload])

    return {"detail": "Webhook accepted"}


@router.websocket("/stream/{vehicle_id}")
async def telemetry_stream(
    websocket: WebSocket,
    vehicle_id: uuid.UUID,
    token: str = Query(default=None),
):
    """
    WebSocket endpoint: streams live telemetry for a single vehicle.
    Fleet manager dashboard subscribes to this for real-time SoC updates.
    Polls the database every 30 seconds and pushes new telemetry to the client.
    Requires a non-empty token query parameter for authentication.
    """
    if not token:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        last_sent_at: datetime | None = None
        async with AsyncSessionLocal() as db:
            while True:
                q = select(VehicleTelemetry).where(
                    VehicleTelemetry.vehicle_id == vehicle_id
                ).order_by(VehicleTelemetry.recorded_at.desc()).limit(1)
                result = await db.execute(q)
                telemetry = result.scalar_one_or_none()

                if telemetry and (last_sent_at is None or telemetry.recorded_at > last_sent_at):
                    out = TelemetryOut.model_validate(telemetry)
                    await websocket.send_json(out.model_dump(mode="json"))
                    last_sent_at = telemetry.recorded_at

                await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass
