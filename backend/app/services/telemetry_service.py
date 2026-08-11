"""
ChargeMesh — Telemetry Processing Service
Handles batch telemetry processing: vehicle state updates, thermal checks, dispatch evaluation.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.vehicle import Vehicle


async def process_single_record(
    db: AsyncSession,
    record: dict,
    org_id: Optional[uuid.UUID] = None,
) -> None:
    """
    Process a single telemetry record:
    1. Update vehicle status from telemetry
    2. Run thermal check
    3. Run dispatch evaluation
    """
    vehicle_id = uuid.UUID(str(record["vehicle_id"]))
    recorded_at = record["recorded_at"]
    if isinstance(recorded_at, str):
        from dateutil import parser
        recorded_at = parser.parse(recorded_at)

    battery_temp = record.get("battery_temp_celsius")
    battery_id_str = record.get("battery_id")
    battery_id = uuid.UUID(battery_id_str) if battery_id_str else None
    soc = record.get("state_of_charge")
    is_charging = record.get("is_charging", False)

    # Load vehicle
    v_result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    vehicle = v_result.scalar_one_or_none()
    if not vehicle:
        return

    if org_id is None:
        org_id = vehicle.org_id

    # Update vehicle status from telemetry
    if is_charging and vehicle.status != "charging":
        vehicle.status = "charging"
        db.add(vehicle)
    elif not is_charging and vehicle.status == "charging":
        vehicle.status = "active"
        db.add(vehicle)

    # If battery_id in telemetry changed, it indicates a swap occurred
    if battery_id and vehicle.current_battery_id and vehicle.current_battery_id != battery_id:
        print(
            f"[ChargeMesh] [TELEMETRY] Battery change detected on vehicle {vehicle.registration_number}: "
            f"{vehicle.current_battery_id} → {battery_id} (swap inferred from telemetry)"
        )
        vehicle.current_battery_id = battery_id
        db.add(vehicle)

    # Run thermal check if temperature data is available
    if battery_temp is not None:
        from app.services.thermal_service import run_thermal_check
        await run_thermal_check(
            db=db,
            vehicle_id=vehicle_id,
            battery_id=battery_id,
            battery_temp_celsius=float(battery_temp),
            ambient_temp_celsius=record.get("ambient_temp_celsius"),
            recorded_at=recorded_at,
            org_id=org_id,
        )

    # Run dispatch evaluation if SoC is available
    if soc is not None:
        from app.services.dispatch_service import evaluate_vehicle_dispatch
        from app.models.telemetry import VehicleTelemetry

        # Get the latest telemetry object
        tel_result = await db.execute(
            select(VehicleTelemetry)
            .where(
                VehicleTelemetry.vehicle_id == vehicle_id,
                VehicleTelemetry.recorded_at == recorded_at,
            )
        )
        telemetry_obj = tel_result.scalar_one_or_none()
        if telemetry_obj:
            await evaluate_vehicle_dispatch(
                db=db,
                vehicle=vehicle,
                latest_telemetry=telemetry_obj,
                remaining_delivery_km=0.0,  # integrate with dispatch system when available
            )
