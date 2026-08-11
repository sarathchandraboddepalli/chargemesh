"""ChargeMesh — Thermal Intelligence API Routes"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import CurrentOrg, DB
from app.config import settings
from app.models.battery import Battery
from app.models.thermal import ThermalAlert
from app.schemas.thermal import BatteryThermalHistory, ThermalAlertOut, ThermalThresholdUpdate

router = APIRouter()


@router.get("/alerts", response_model=list[ThermalAlertOut])
async def active_thermal_alerts(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(ThermalAlert)
        .where(ThermalAlert.org_id == current_org.id, ThermalAlert.is_resolved == False)
        .order_by(ThermalAlert.created_at.desc())
    )
    return result.scalars().all()


@router.get("/batteries/{battery_id}", response_model=BatteryThermalHistory)
async def battery_thermal_history(battery_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    battery_result = await db.execute(
        select(Battery).where(Battery.id == battery_id, Battery.owner_org_id == current_org.id)
    )
    battery = battery_result.scalar_one_or_none()
    if not battery:
        raise HTTPException(status_code=404, detail="Battery not found")

    alerts_result = await db.execute(
        select(ThermalAlert)
        .where(ThermalAlert.battery_id == battery_id)
        .order_by(ThermalAlert.created_at.desc())
        .limit(50)
    )
    alerts = alerts_result.scalars().all()

    stress = float(battery.accumulated_thermal_stress or 0)
    if stress < 10:
        label = "low"
    elif stress < 50:
        label = "moderate"
    elif stress < 200:
        label = "high"
    else:
        label = "critical"

    # Peak temp from alerts
    peak_temp = None
    for a in alerts:
        if a.temperature_celsius and (peak_temp is None or float(a.temperature_celsius) > peak_temp):
            peak_temp = float(a.temperature_celsius)

    return BatteryThermalHistory(
        battery_id=battery_id,
        accumulated_stress=stress,
        stress_score_label=label,
        peak_temp_celsius=peak_temp,
        alerts=[ThermalAlertOut.model_validate(a) for a in alerts],
    )


@router.get("/fleet-summary")
async def fleet_thermal_summary(current_org: CurrentOrg, db: DB):
    batteries_result = await db.execute(
        select(Battery).where(Battery.owner_org_id == current_org.id)
    )
    batteries = batteries_result.scalars().all()

    flagged = [b for b in batteries if b.is_flagged]
    active_alerts = await db.execute(
        select(func.count(ThermalAlert.id))
        .where(ThermalAlert.org_id == current_org.id, ThermalAlert.is_resolved == False)
    )
    alert_count = active_alerts.scalar() or 0

    avg_stress = (
        sum(float(b.accumulated_thermal_stress or 0) for b in batteries) / len(batteries)
        if batteries else 0
    )

    return {
        "total_batteries": len(batteries),
        "flagged_batteries": len(flagged),
        "active_alerts": alert_count,
        "average_thermal_stress": round(avg_stress, 2),
    }


@router.post("/thresholds")
async def update_thresholds(payload: ThermalThresholdUpdate, current_org: CurrentOrg):
    # In production: persist per-org thresholds to database
    print(
        f"[ChargeMesh] [MOCK] Would update thermal thresholds for org {current_org.id}: "
        f"warning={payload.warning_celsius}, critical={payload.critical_celsius}"
    )
    return {
        "warning_celsius": payload.warning_celsius or settings.THERMAL_WARNING_THRESHOLD,
        "critical_celsius": payload.critical_celsius or settings.THERMAL_CRITICAL_THRESHOLD,
    }
