"""
ChargeMesh — Driver Mobile App API Routes
All /driver/* endpoints enforce role='driver'.
Driver location is NOT sent to ChargeMesh unless explicitly consented.
Vehicle location comes from OEM telemetry only.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import DB, CurrentUser, require_role
from app.config import settings
from app.models.battery import BatterySwap
from app.models.dispatch import DispatchRecommendation
from app.models.network import ChargingStation
from app.models.session import ChargingSession
from app.models.telemetry import VehicleTelemetry
from app.models.vehicle import Driver, Vehicle
from app.schemas.battery import SwapCreate
from app.utils.geo_utils import haversine_km

router = APIRouter()

# Enforce driver role on all routes in this module
DriverUser = require_role("driver", "user", "admin")  # drivers or higher


@router.get("/me")
async def driver_profile(current_user: CurrentUser, db: DB):
    result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")
    return {
        "driver_id": str(driver.id),
        "name": driver.name,
        "phone": driver.phone,
        "assigned_vehicle_id": str(driver.assigned_vehicle_id) if driver.assigned_vehicle_id else None,
        "shift_start": driver.shift_start.isoformat() if driver.shift_start else None,
        "shift_end": driver.shift_end.isoformat() if driver.shift_end else None,
    }


@router.get("/vehicle")
async def driver_vehicle(current_user: CurrentUser, db: DB):
    """Current vehicle SoC + estimated range for the driver's assigned vehicle."""
    driver_result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = driver_result.scalar_one_or_none()
    if not driver or not driver.assigned_vehicle_id:
        raise HTTPException(status_code=404, detail="No vehicle assigned")

    tel_result = await db.execute(
        select(VehicleTelemetry)
        .where(VehicleTelemetry.vehicle_id == driver.assigned_vehicle_id)
        .order_by(VehicleTelemetry.recorded_at.desc())
        .limit(1)
    )
    telemetry = tel_result.scalar_one_or_none()

    v_result = await db.execute(select(Vehicle).where(Vehicle.id == driver.assigned_vehicle_id))
    vehicle = v_result.scalar_one_or_none()

    return {
        "vehicle_id": str(vehicle.id) if vehicle else None,
        "registration_number": vehicle.registration_number if vehicle else None,
        "model_name": vehicle.model_name if vehicle else None,
        "status": vehicle.status if vehicle else None,
        "state_of_charge": float(telemetry.state_of_charge) if telemetry and telemetry.state_of_charge else None,
        "estimated_range_km": float(telemetry.estimated_range_km) if telemetry and telemetry.estimated_range_km else None,
        "last_telemetry_at": telemetry.recorded_at.isoformat() if telemetry else None,
        # Note: location is from OEM telemetry, NOT from driver's phone
        "is_charging": telemetry.is_charging if telemetry else False,
    }


@router.get("/recommendation")
async def driver_recommendation(current_user: CurrentUser, db: DB):
    """Current charging recommendation for the driver's vehicle."""
    driver_result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = driver_result.scalar_one_or_none()
    if not driver or not driver.assigned_vehicle_id:
        return {"recommendation": None}

    result = await db.execute(
        select(DispatchRecommendation)
        .where(
            DispatchRecommendation.vehicle_id == driver.assigned_vehicle_id,
            DispatchRecommendation.was_acted_upon.is_(None),
        )
        .order_by(DispatchRecommendation.recommended_at.desc())
        .limit(1)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return {"recommendation": None}

    station = None
    if rec.recommended_station_id:
        s_result = await db.execute(select(ChargingStation).where(ChargingStation.id == rec.recommended_station_id))
        station = s_result.scalar_one_or_none()

    return {
        "recommendation": {
            "id": str(rec.id),
            "trigger_soc": float(rec.trigger_soc) if rec.trigger_soc else None,
            "recommended_at": rec.recommended_at.isoformat(),
            "station": {
                "id": str(station.id),
                "name": station.name,
                "address": station.address,
                "latitude": float(station.latitude) if station.latitude else None,
                "longitude": float(station.longitude) if station.longitude else None,
                "available_connectors": station.available_connectors,
                "pricing_per_kwh": float(station.pricing_per_kwh) if station.pricing_per_kwh else None,
            } if station else None,
        }
    }


@router.get("/stations/nearby")
async def driver_nearby_stations(
    current_user: CurrentUser,
    db: DB,
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(5.0),
):
    """
    Nearby available charging stations for the driver.
    Latitude/longitude come from the driver's device for this query ONLY —
    they are used client-side for sorting and are not stored server-side.
    """
    result = await db.execute(
        select(ChargingStation).where(
            ChargingStation.available_connectors > 0,
            ChargingStation.is_operational == True,
            ChargingStation.latitude.isnot(None),
        )
    )
    stations = result.scalars().all()

    nearby = []
    for s in stations:
        dist = haversine_km(latitude, longitude, float(s.latitude), float(s.longitude))
        if dist <= radius_km:
            nearby.append({
                "id": str(s.id),
                "name": s.name,
                "address": s.address,
                "distance_km": round(dist, 2),
                "available_connectors": s.available_connectors,
                "total_connectors": s.total_connectors,
                "pricing_per_kwh": float(s.pricing_per_kwh) if s.pricing_per_kwh else None,
                "latitude": float(s.latitude),
                "longitude": float(s.longitude),
            })

    nearby.sort(key=lambda x: x["distance_km"])
    return nearby


@router.post("/sessions/start", status_code=status.HTTP_201_CREATED)
async def driver_start_session(
    station_id: uuid.UUID,
    current_user: CurrentUser,
    db: DB,
):
    driver_result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = driver_result.scalar_one_or_none()
    if not driver or not driver.assigned_vehicle_id:
        raise HTTPException(status_code=404, detail="No vehicle assigned")

    s_result = await db.execute(select(ChargingStation).where(ChargingStation.id == station_id))
    station = s_result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    if not station.is_operational:
        raise HTTPException(status_code=409, detail="Station is not operational")

    session = ChargingSession(
        vehicle_id=driver.assigned_vehicle_id,
        driver_id=driver.id,
        station_id=station_id,
        network_id=station.network_id,
        status="active",
        booking_type="driver",
        started_at=datetime.now(timezone.utc),
        booked_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.flush()
    return {"session_id": str(session.id), "status": "active"}


@router.post("/sessions/{session_id}/stop")
async def driver_stop_session(session_id: uuid.UUID, current_user: CurrentUser, db: DB):
    driver_result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = driver_result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    result = await db.execute(
        select(ChargingSession).where(
            ChargingSession.id == session_id,
            ChargingSession.driver_id == driver.id,
            ChargingSession.status == "active",
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    now = datetime.now(timezone.utc)
    session.status = "completed"
    session.ended_at = now
    if session.started_at:
        session.duration_minutes = int((now - session.started_at).total_seconds() / 60)
    db.add(session)
    return {"session_id": str(session_id), "status": "completed"}


@router.get("/sessions/history")
async def driver_session_history(current_user: CurrentUser, db: DB):
    driver_result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = driver_result.scalar_one_or_none()
    if not driver:
        return []

    result = await db.execute(
        select(ChargingSession)
        .where(ChargingSession.driver_id == driver.id, ChargingSession.status == "completed")
        .order_by(ChargingSession.ended_at.desc())
        .limit(50)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "station_id": str(s.station_id) if s.station_id else None,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "duration_minutes": s.duration_minutes,
            "energy_delivered_kwh": float(s.energy_delivered_kwh) if s.energy_delivered_kwh else None,
            "cost_inr": float(s.cost_inr) if s.cost_inr else None,
        }
        for s in sessions
    ]


@router.post("/swaps")
async def driver_record_swap(payload: SwapCreate, current_user: CurrentUser, db: DB):
    """Driver records a battery swap from the mobile app."""
    driver_result = await db.execute(select(Driver).where(Driver.user_id == current_user.id))
    driver = driver_result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # Delegate to the swap service (same validation as fleet API)
    from app.api.v1.swaps import record_swap
    # Create a minimal org context
    from app.models.org import Organization
    org_result = await db.execute(select(Organization).where(Organization.id == driver.org_id))
    org = org_result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=403, detail="No organization")

    # Record swap with driver context
    from app.models.battery import BatterySwap as BatterySwapModel
    swap = BatterySwapModel(
        vehicle_id=payload.vehicle_id,
        driver_id=driver.id,
        removed_battery_id=payload.removed_battery_id,
        installed_battery_id=payload.installed_battery_id,
        baas_vendor_org_id=payload.baas_vendor_org_id,
        swap_station_name=payload.swap_station_name,
        removed_battery_soc=payload.removed_battery_soc,
    )
    db.add(swap)
    await db.flush()
    return {"swap_id": str(swap.id), "status": "recorded"}
