"""ChargeMesh — Battery Swap Events API"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentOrg, DB
from app.models.battery import Battery, BatterySwap
from app.models.vehicle import Driver, Vehicle
from app.schemas.battery import SwapCreate, SwapOut
from app.services.settlement_service import calculate_swap_settlement

router = APIRouter()


@router.post("", response_model=SwapOut, status_code=status.HTTP_201_CREATED)
async def record_swap(payload: SwapCreate, current_org: CurrentOrg, db: DB):
    """
    Record a battery swap event.
    IMPORTANT: SoH update and swap event creation are in the SAME transaction
    to prevent ledger corruption from partial writes.
    """
    # Verify vehicle belongs to org
    v_result = await db.execute(
        select(Vehicle).where(Vehicle.id == payload.vehicle_id, Vehicle.org_id == current_org.id)
    )
    vehicle = v_result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    removed_battery = None
    installed_battery = None

    if payload.removed_battery_id:
        result = await db.execute(select(Battery).where(Battery.id == payload.removed_battery_id))
        removed_battery = result.scalar_one_or_none()

    if payload.installed_battery_id:
        result = await db.execute(select(Battery).where(Battery.id == payload.installed_battery_id))
        installed_battery = result.scalar_one_or_none()

    # Calculate kWh consumed since last swap for the removed battery
    kwh_consumed = None
    degradation = None
    settlement_amount = None

    if removed_battery and payload.removed_battery_soc is not None:
        # Estimate kWh consumed: (SoH-adjusted capacity) × (100 - current SoC) / 100
        cap = float(removed_battery.nominal_capacity_kwh or 0)
        soh_factor = float(removed_battery.current_soh or 100) / 100
        kwh_consumed = cap * soh_factor * (100 - payload.removed_battery_soc) / 100

        # Calculate settlement amounts using the service
        from app.services.settlement_service import calculate_swap_settlement
        settlement_data = await calculate_swap_settlement(
            db=db,
            battery=removed_battery,
            fleet_org_id=current_org.id,
            kwh_consumed=kwh_consumed,
        )
        degradation = settlement_data.get("degradation_this_session")
        settlement_amount = settlement_data.get("settlement_amount_inr")

    # === TRANSACTION: SoH update + swap creation must be atomic ===
    swap = BatterySwap(
        vehicle_id=payload.vehicle_id,
        removed_battery_id=payload.removed_battery_id,
        installed_battery_id=payload.installed_battery_id,
        baas_vendor_org_id=payload.baas_vendor_org_id,
        swap_station_name=payload.swap_station_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        removed_battery_soc=payload.removed_battery_soc,
        removed_battery_soh=float(removed_battery.current_soh) if removed_battery and removed_battery.current_soh else None,
        removed_battery_temp=payload.removed_battery_temp,
        installed_battery_soc=payload.installed_battery_soc,
        installed_battery_soh=float(installed_battery.current_soh) if installed_battery and installed_battery.current_soh else None,
        kwh_consumed_this_session=kwh_consumed,
        degradation_this_session=degradation,
        settlement_amount_inr=settlement_amount,
        settlement_status="pending",
    )
    db.add(swap)

    # Update battery records atomically with the swap
    if removed_battery:
        removed_battery.status = "available"
        removed_battery.current_vehicle_id = None
        if kwh_consumed:
            removed_battery.total_kwh_delivered = (
                float(removed_battery.total_kwh_delivered or 0) + kwh_consumed
            )
        if degradation:
            new_soh = float(removed_battery.current_soh or 100) - degradation
            removed_battery.current_soh = max(0, new_soh)
        db.add(removed_battery)

    if installed_battery:
        installed_battery.status = "installed"
        installed_battery.current_vehicle_id = payload.vehicle_id
        db.add(installed_battery)

    # Update vehicle's current battery
    vehicle.current_battery_id = payload.installed_battery_id
    vehicle.status = "swapping"
    db.add(vehicle)

    await db.flush()
    return swap


@router.get("/{swap_id}", response_model=SwapOut)
async def get_swap(swap_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(BatterySwap)
        .join(Vehicle, Vehicle.id == BatterySwap.vehicle_id)
        .where(BatterySwap.id == swap_id, Vehicle.org_id == current_org.id)
    )
    swap = result.scalar_one_or_none()
    if not swap:
        raise HTTPException(status_code=404, detail="Swap event not found")
    return swap


@router.get("", response_model=list[SwapOut])
async def list_swaps(
    current_org: CurrentOrg,
    db: DB,
    vehicle_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    q = (
        select(BatterySwap)
        .join(Vehicle, Vehicle.id == BatterySwap.vehicle_id)
        .where(Vehicle.org_id == current_org.id)
    )
    if vehicle_id:
        q = q.where(BatterySwap.vehicle_id == vehicle_id)
    q = q.order_by(BatterySwap.swapped_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return result.scalars().all()
