"""ChargeMesh — Analytics and Reporting API Routes"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentOrg, DB
from app.models.battery import Battery
from app.models.dispatch import DispatchRecommendation
from app.models.session import ChargingSession
from app.models.vehicle import Vehicle

router = APIRouter()


@router.get("/downtime")
async def charging_downtime(
    current_org: CurrentOrg,
    db: DB,
    days: int = Query(30, ge=1, le=90),
):
    """Charging downtime per vehicle: % of operational hours spent unplanned charging."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            ChargingSession.vehicle_id,
            func.count(ChargingSession.id).label("session_count"),
            func.sum(ChargingSession.duration_minutes).label("total_charging_minutes"),
            func.sum(ChargingSession.energy_delivered_kwh).label("total_kwh"),
        )
        .join(Vehicle, Vehicle.id == ChargingSession.vehicle_id)
        .where(
            Vehicle.org_id == current_org.id,
            ChargingSession.started_at >= since,
            ChargingSession.status == "completed",
        )
        .group_by(ChargingSession.vehicle_id)
    )
    rows = result.all()
    return [
        {
            "vehicle_id": str(row.vehicle_id),
            "session_count": row.session_count,
            "total_charging_minutes": row.total_charging_minutes or 0,
            "total_kwh": float(row.total_kwh or 0),
        }
        for row in rows
    ]


@router.get("/soc-distribution")
async def soc_distribution(current_org: CurrentOrg, db: DB):
    """Current SoC distribution across fleet."""
    from app.models.telemetry import VehicleTelemetry

    result = await db.execute(
        select(Vehicle).where(Vehicle.org_id == current_org.id, Vehicle.is_active == True)
    )
    vehicles = result.scalars().all()

    buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0, "unknown": 0}
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
                buckets["0-20"] += 1
            elif soc <= 40:
                buckets["20-40"] += 1
            elif soc <= 60:
                buckets["40-60"] += 1
            elif soc <= 80:
                buckets["60-80"] += 1
            else:
                buckets["80-100"] += 1
        else:
            buckets["unknown"] += 1
    return buckets


@router.get("/dispatch-accuracy")
async def dispatch_accuracy(
    current_org: CurrentOrg,
    db: DB,
    days: int = Query(30, ge=1, le=90),
):
    """Percentage of dispatch recommendations that were acted upon."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            func.count(DispatchRecommendation.id).label("total"),
            func.sum(
                func.cast(DispatchRecommendation.was_acted_upon == True, func.Integer())
            ).label("acted_upon"),
        )
        .where(
            DispatchRecommendation.org_id == current_org.id,
            DispatchRecommendation.recommended_at >= since,
            DispatchRecommendation.was_acted_upon.isnot(None),
        )
    )
    row = result.one()
    total = row.total or 0
    acted = row.acted_upon or 0
    accuracy = round((acted / total * 100) if total > 0 else 0, 1)
    return {"total_recommendations": total, "acted_upon": acted, "accuracy_pct": accuracy}


@router.get("/degradation-trend")
async def degradation_trend(current_org: CurrentOrg, db: DB):
    """Battery degradation rate vs OEM benchmark."""
    result = await db.execute(
        select(Battery).where(Battery.owner_org_id == current_org.id)
    )
    batteries = result.scalars().all()

    data = []
    for b in batteries:
        if b.current_soh and b.cycle_count and b.cycle_count > 0:
            # OEM benchmark: ~0.05% SoH loss per cycle for NMC batteries
            oem_expected_soh = max(0, 100 - (b.cycle_count * 0.05))
            actual_soh = float(b.current_soh)
            variance = actual_soh - oem_expected_soh
            data.append({
                "battery_id": str(b.id),
                "model": b.model,
                "cycle_count": b.cycle_count,
                "actual_soh": actual_soh,
                "oem_benchmark_soh": round(oem_expected_soh, 2),
                "variance_pct": round(variance, 2),
                "is_underperforming": variance < -5,  # >5% worse than benchmark
            })
    return data


@router.get("/station-utilization")
async def station_utilization(
    current_org: CurrentOrg,
    db: DB,
    days: int = Query(30, ge=1, le=90),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            ChargingSession.station_id,
            func.count(ChargingSession.id).label("session_count"),
            func.sum(ChargingSession.energy_delivered_kwh).label("total_kwh"),
        )
        .join(Vehicle, Vehicle.id == ChargingSession.vehicle_id)
        .where(
            Vehicle.org_id == current_org.id,
            ChargingSession.started_at >= since,
            ChargingSession.station_id.isnot(None),
        )
        .group_by(ChargingSession.station_id)
    )
    return [
        {
            "station_id": str(row.station_id),
            "session_count": row.session_count,
            "total_kwh": float(row.total_kwh or 0),
        }
        for row in result.all()
    ]
