"""ChargeMesh — Fleet Management API Routes"""

import csv
import io
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentOrg, CurrentUser, DB
from app.models.telemetry import VehicleTelemetry
from app.models.vehicle import Driver, Vehicle
from app.schemas.telemetry import TelemetryOut
from app.schemas.vehicle import (
    FleetSummary,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
    VehicleWithSoC,
)

router = APIRouter()

STALE_THRESHOLD_MINUTES = 10


async def enrich_with_soc(vehicle: Vehicle, db) -> VehicleWithSoC:
    """Fetch latest telemetry and attach SoC data to vehicle."""
    result = await db.execute(
        select(VehicleTelemetry)
        .where(VehicleTelemetry.vehicle_id == vehicle.id)
        .order_by(VehicleTelemetry.recorded_at.desc())
        .limit(1)
    )
    telemetry = result.scalar_one_or_none()

    out = VehicleWithSoC.model_validate(vehicle)
    if telemetry:
        out.current_soc = float(telemetry.state_of_charge) if telemetry.state_of_charge else None
        out.current_latitude = float(telemetry.latitude) if telemetry.latitude else None
        out.current_longitude = float(telemetry.longitude) if telemetry.longitude else None
        out.last_telemetry_at = telemetry.recorded_at
        out.estimated_range_km = float(telemetry.estimated_range_km) if telemetry.estimated_range_km else None
        stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_THRESHOLD_MINUTES)
        out.is_stale = telemetry.recorded_at < stale_cutoff
    return out


@router.get("/summary", response_model=FleetSummary)
async def fleet_summary(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Vehicle).where(Vehicle.org_id == current_org.id, Vehicle.is_active == True)
    )
    vehicles = result.scalars().all()

    distribution = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    at_risk = 0
    charging = 0

    for v in vehicles:
        tel_result = await db.execute(
            select(VehicleTelemetry)
            .where(VehicleTelemetry.vehicle_id == v.id)
            .order_by(VehicleTelemetry.recorded_at.desc())
            .limit(1)
        )
        tel = tel_result.scalar_one_or_none()
        if tel and tel.state_of_charge is not None:
            soc = float(tel.state_of_charge)
            if soc <= 20:
                distribution["0-20"] += 1
                at_risk += 1
            elif soc <= 40:
                distribution["20-40"] += 1
            elif soc <= 60:
                distribution["40-60"] += 1
            elif soc <= 80:
                distribution["60-80"] += 1
            else:
                distribution["80-100"] += 1
        if v.status == "charging":
            charging += 1

    return FleetSummary(
        total_vehicles=len(vehicles),
        active_vehicles=sum(1 for v in vehicles if v.status == "active"),
        charging_vehicles=charging,
        at_risk_vehicles=at_risk,
        soc_distribution=distribution,
        vehicles_with_recommendations=0,  # populated by dispatch service
        active_sessions=charging,
    )


@router.get("/vehicles", response_model=list[VehicleWithSoC])
async def list_vehicles(
    current_org: CurrentOrg,
    db: DB,
    zone: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = select(Vehicle).where(Vehicle.org_id == current_org.id, Vehicle.is_active == True)
    if zone:
        q = q.where(Vehicle.zone == zone)
    if status_filter:
        q = q.where(Vehicle.status == status_filter)
    q = q.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(q)
    vehicles = result.scalars().all()
    return [await enrich_with_soc(v, db) for v in vehicles]


@router.post("/vehicles", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
async def register_vehicle(payload: VehicleCreate, current_org: CurrentOrg, db: DB):
    existing = await db.execute(
        select(Vehicle).where(Vehicle.registration_number == payload.registration_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Registration number already exists")

    vehicle = Vehicle(
        org_id=current_org.id,
        **payload.model_dump(exclude_none=True),
    )
    db.add(vehicle)
    await db.flush()
    return vehicle


@router.get("/vehicles/{vehicle_id}", response_model=VehicleWithSoC)
async def get_vehicle(vehicle_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.org_id == current_org.id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return await enrich_with_soc(vehicle, db)


@router.put("/vehicles/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(vehicle_id: uuid.UUID, payload: VehicleUpdate, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.org_id == current_org.id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(vehicle, field, value)
    db.add(vehicle)
    return vehicle


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deregister_vehicle(vehicle_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.org_id == current_org.id)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.is_active = False
    db.add(vehicle)


@router.post("/vehicles/bulk-import", status_code=status.HTTP_201_CREATED)
async def bulk_import_vehicles(
    current_org: CurrentOrg,
    db: DB,
    file: UploadFile = File(...),
):
    """Bulk import vehicles from CSV file.
    Expected columns: registration_number, model_name, zone, battery_capacity_kwh, max_range_km
    """
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    created = 0
    skipped = 0
    errors = []

    for i, row in enumerate(reader, start=2):
        reg = row.get("registration_number", "").strip()
        if not reg:
            errors.append(f"Row {i}: missing registration_number")
            continue

        existing = await db.execute(select(Vehicle).where(Vehicle.registration_number == reg))
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        try:
            vehicle = Vehicle(
                org_id=current_org.id,
                registration_number=reg,
                model_name=row.get("model_name", "").strip() or None,
                zone=row.get("zone", "").strip() or None,
                battery_capacity_kwh=float(row["battery_capacity_kwh"]) if row.get("battery_capacity_kwh") else None,
                max_range_km=float(row["max_range_km"]) if row.get("max_range_km") else None,
            )
            db.add(vehicle)
            created += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    return {"created": created, "skipped": skipped, "errors": errors}


@router.get("/vehicles/{vehicle_id}/telemetry", response_model=list[TelemetryOut])
async def vehicle_telemetry(
    vehicle_id: uuid.UUID,
    current_org: CurrentOrg,
    db: DB,
    hours: int = Query(24, ge=1, le=168),
):
    # Verify vehicle belongs to org
    v_result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.org_id == current_org.id)
    )
    if not v_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Vehicle not found")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(VehicleTelemetry)
        .where(
            VehicleTelemetry.vehicle_id == vehicle_id,
            VehicleTelemetry.recorded_at >= since,
        )
        .order_by(VehicleTelemetry.recorded_at.asc())
    )
    return result.scalars().all()
