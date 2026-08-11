"""
ChargeMesh — Dispatch Service
Charge-to-complete calculation and nearest available station selection.

Dispatch trigger: SoC < DISPATCH_SOC_THRESHOLD AND estimated_range < remaining_km + safety_buffer_km
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.dispatch import DispatchRecommendation
from app.models.network import ChargingStation
from app.models.telemetry import VehicleTelemetry
from app.models.vehicle import Vehicle
from app.utils.geo_utils import haversine_km


async def evaluate_vehicle_dispatch(
    db: AsyncSession,
    vehicle: Vehicle,
    latest_telemetry: VehicleTelemetry,
    remaining_delivery_km: float = 0.0,
) -> Optional[DispatchRecommendation]:
    """
    Evaluate whether a vehicle needs an immediate charging recommendation.

    Algorithm:
    1. If SoC < DISPATCH_SOC_THRESHOLD (default: 25%):
        a. Calculate estimated_range from telemetry
        b. If estimated_range < remaining_delivery_km + SAFETY_BUFFER_KM: trigger
        c. Find nearest available compatible charging station
        d. Create dispatch_recommendations record
    2. Return the recommendation or None if no action needed.

    Returns: DispatchRecommendation if triggered, else None
    """
    if latest_telemetry.state_of_charge is None:
        return None

    soc = float(latest_telemetry.state_of_charge)
    estimated_range = float(latest_telemetry.estimated_range_km or 0)

    # Trigger condition: low SoC AND insufficient range to complete deliveries
    soc_trigger = soc < settings.DISPATCH_SOC_THRESHOLD
    range_trigger = estimated_range < (remaining_delivery_km + settings.DISPATCH_SAFETY_BUFFER_KM)

    if not soc_trigger:
        return None  # SoC is acceptable — no action

    # Even if no delivery data, trigger on very low SoC
    if soc >= settings.DISPATCH_SOC_THRESHOLD and not range_trigger:
        return None

    # Find nearest available charging station
    station = await find_nearest_available_station(
        db=db,
        latitude=float(latest_telemetry.latitude) if latest_telemetry.latitude else None,
        longitude=float(latest_telemetry.longitude) if latest_telemetry.longitude else None,
        vehicle_model=vehicle.model_name,
    )

    # Predict when battery will deplete at current consumption rate
    predicted_depletion = None
    if vehicle.max_range_km and soc > 0:
        # Estimate km/hour consumed based on vehicle type
        avg_speed = float(latest_telemetry.speed_kmh or 20)  # default 20 km/h for delivery
        if avg_speed > 0:
            range_left_hours = estimated_range / avg_speed
            predicted_depletion = datetime.now(timezone.utc) + timedelta(hours=range_left_hours)

    recommendation = DispatchRecommendation(
        org_id=vehicle.org_id,
        vehicle_id=vehicle.id,
        recommended_station_id=station.id if station else None,
        trigger_soc=soc,
        predicted_depletion_at=predicted_depletion,
    )
    db.add(recommendation)
    await db.flush()

    print(
        f"[ChargeMesh] [DISPATCH] Vehicle {vehicle.registration_number} SoC={soc:.1f}% "
        f"range={estimated_range:.1f}km remaining_km={remaining_delivery_km:.1f}km "
        f"→ Recommendation: {station.name if station else 'no station found'}"
    )
    return recommendation


async def find_nearest_available_station(
    db: AsyncSession,
    latitude: Optional[float],
    longitude: Optional[float],
    vehicle_model: Optional[str] = None,
    max_radius_km: float = 15.0,
) -> Optional[ChargingStation]:
    """
    Find the nearest available charging station within max_radius_km.
    Filters to operational stations with available connectors.
    Uses Haversine distance since earthdistance PostGIS extension is optional at dev time.
    """
    result = await db.execute(
        select(ChargingStation).where(
            ChargingStation.is_operational == True,
            ChargingStation.available_connectors > 0,
            ChargingStation.latitude.isnot(None),
            ChargingStation.longitude.isnot(None),
        )
    )
    stations = result.scalars().all()

    if not stations:
        return None

    if latitude is None or longitude is None:
        # No location data — return any available station
        return stations[0]

    nearest = None
    min_dist = float("inf")
    for s in stations:
        dist = haversine_km(latitude, longitude, float(s.latitude), float(s.longitude))
        if dist <= max_radius_km and dist < min_dist:
            min_dist = dist
            nearest = s

    return nearest
