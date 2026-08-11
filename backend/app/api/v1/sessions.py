"""ChargeMesh — Charging Session API Routes"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentOrg, DB
from app.models.network import ChargingStation
from app.models.session import ChargingSession
from app.models.vehicle import Vehicle
from app.schemas.session import SessionBookRequest, SessionOut

router = APIRouter()


@router.post("/book", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def book_session(payload: SessionBookRequest, current_org: CurrentOrg, db: DB):
    # Verify vehicle belongs to org
    v_result = await db.execute(
        select(Vehicle).where(Vehicle.id == payload.vehicle_id, Vehicle.org_id == current_org.id)
    )
    if not v_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Verify station exists
    s_result = await db.execute(select(ChargingStation).where(ChargingStation.id == payload.station_id))
    station = s_result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    if not station.is_operational:
        raise HTTPException(status_code=409, detail="Station is not operational")

    session = ChargingSession(
        vehicle_id=payload.vehicle_id,
        station_id=payload.station_id,
        network_id=station.network_id,
        status="booked",
        booking_type=payload.booking_type,
        booked_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()
    return session


@router.get("/active", response_model=list[SessionOut])
async def active_sessions(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingSession)
        .join(Vehicle, Vehicle.id == ChargingSession.vehicle_id)
        .where(Vehicle.org_id == current_org.id, ChargingSession.status == "active")
    )
    return result.scalars().all()


@router.get("", response_model=list[SessionOut])
async def list_sessions(
    current_org: CurrentOrg,
    db: DB,
    vehicle_id: uuid.UUID | None = Query(None),
    session_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = (
        select(ChargingSession)
        .join(Vehicle, Vehicle.id == ChargingSession.vehicle_id)
        .where(Vehicle.org_id == current_org.id)
    )
    if vehicle_id:
        q = q.where(ChargingSession.vehicle_id == vehicle_id)
    if session_status:
        q = q.where(ChargingSession.status == session_status)
    q = q.order_by(ChargingSession.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(session_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingSession)
        .join(Vehicle, Vehicle.id == ChargingSession.vehicle_id)
        .where(ChargingSession.id == session_id, Vehicle.org_id == current_org.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/start", response_model=SessionOut)
async def start_session(session_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingSession)
        .join(Vehicle, Vehicle.id == ChargingSession.vehicle_id)
        .where(ChargingSession.id == session_id, Vehicle.org_id == current_org.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "booked":
        raise HTTPException(status_code=409, detail=f"Session is already {session.status}")

    session.status = "active"
    session.started_at = datetime.now(timezone.utc)

    # Update vehicle status
    v_result = await db.execute(select(Vehicle).where(Vehicle.id == session.vehicle_id))
    vehicle = v_result.scalar_one()
    vehicle.status = "charging"
    db.add(vehicle)
    db.add(session)
    return session


@router.post("/{session_id}/stop", response_model=SessionOut)
async def stop_session(session_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ChargingSession)
        .join(Vehicle, Vehicle.id == ChargingSession.vehicle_id)
        .where(ChargingSession.id == session_id, Vehicle.org_id == current_org.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=409, detail=f"Session is not active (status: {session.status})")

    now = datetime.now(timezone.utc)
    session.status = "completed"
    session.ended_at = now
    if session.started_at:
        delta = now - session.started_at
        session.duration_minutes = int(delta.total_seconds() / 60)

    # Update vehicle status
    v_result = await db.execute(select(Vehicle).where(Vehicle.id == session.vehicle_id))
    vehicle = v_result.scalar_one()
    vehicle.status = "active"
    db.add(vehicle)
    db.add(session)
    return session
