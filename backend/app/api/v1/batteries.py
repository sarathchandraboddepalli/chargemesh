"""ChargeMesh — Battery Registry API Routes"""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentOrg, DB
from app.models.battery import Battery, BatterySwap
from app.models.thermal import ThermalAlert
from app.schemas.battery import BatteryCreate, BatteryOut

router = APIRouter()


@router.get("", response_model=list[BatteryOut])
async def list_batteries(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Battery).where(Battery.owner_org_id == current_org.id)
    )
    return result.scalars().all()


@router.post("", response_model=BatteryOut, status_code=status.HTTP_201_CREATED)
async def register_battery(payload: BatteryCreate, current_org: CurrentOrg, db: DB):
    battery = Battery(owner_org_id=current_org.id, **payload.model_dump(exclude_none=True))
    db.add(battery)
    await db.flush()
    return battery


@router.get("/{battery_id}", response_model=BatteryOut)
async def get_battery(battery_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Battery).where(Battery.id == battery_id, Battery.owner_org_id == current_org.id)
    )
    battery = result.scalar_one_or_none()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")
    return battery


@router.get("/{battery_id}/events")
async def battery_events(battery_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    """All swap events and charge sessions for this battery."""
    result = await db.execute(
        select(Battery).where(Battery.id == battery_id, Battery.owner_org_id == current_org.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Battery not found")

    swaps_result = await db.execute(
        select(BatterySwap).where(
            (BatterySwap.removed_battery_id == battery_id) |
            (BatterySwap.installed_battery_id == battery_id)
        ).order_by(BatterySwap.swapped_at.desc())
    )
    return {"swaps": swaps_result.scalars().all()}


@router.get("/{battery_id}/health-report")
async def battery_health_report(battery_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(Battery).where(Battery.id == battery_id, Battery.owner_org_id == current_org.id)
    )
    battery = result.scalar_one_or_none()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")

    # Thermal alerts
    alerts_result = await db.execute(
        select(ThermalAlert).where(ThermalAlert.battery_id == battery_id)
        .order_by(ThermalAlert.created_at.desc()).limit(20)
    )

    # Estimate remaining useful life based on SoH
    soh = float(battery.current_soh) if battery.current_soh else 100.0
    rul_estimate = "Unknown"
    if soh > 80:
        rul_estimate = ">18 months"
    elif soh > 60:
        rul_estimate = "6-18 months"
    elif soh > 40:
        rul_estimate = "< 6 months — schedule replacement"
    else:
        rul_estimate = "Replace immediately"

    return {
        "battery_id": battery_id,
        "current_soh": battery.current_soh,
        "cycle_count": battery.cycle_count,
        "total_kwh_delivered": battery.total_kwh_delivered,
        "accumulated_thermal_stress": battery.accumulated_thermal_stress,
        "is_flagged": battery.is_flagged,
        "flag_reason": battery.flag_reason,
        "estimated_rul": rul_estimate,
        "thermal_alert_count": len(alerts_result.scalars().all()),
    }
