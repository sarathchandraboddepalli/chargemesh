"""ChargeMesh — Admin API Routes (platform_admin role required)"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser, require_role
from app.models.org import Organization
from app.models.session import ChargingSession
from app.models.vehicle import Vehicle

router = APIRouter()
AdminRequired = require_role("admin")


@router.get("/orgs")
async def list_all_orgs(db: DB, _: CurrentUser = AdminRequired):
    result = await db.execute(select(Organization))
    orgs = result.scalars().all()
    return [{"id": str(o.id), "name": o.name, "org_type": o.org_type, "tier": o.tier} for o in orgs]


@router.get("/platform-stats")
async def platform_stats(db: DB, _: CurrentUser = AdminRequired):
    total_vehicles = (await db.execute(select(func.count(Vehicle.id)))).scalar() or 0
    total_orgs = (await db.execute(select(func.count(Organization.id)))).scalar() or 0

    from datetime import datetime, timezone, timedelta
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    sessions_today = (
        await db.execute(
            select(func.count(ChargingSession.id))
            .where(ChargingSession.created_at >= today)
        )
    ).scalar() or 0

    kwh_today = (
        await db.execute(
            select(func.sum(ChargingSession.energy_delivered_kwh))
            .where(ChargingSession.created_at >= today)
        )
    ).scalar() or 0

    return {
        "total_vehicles": total_vehicles,
        "total_organizations": total_orgs,
        "sessions_today": sessions_today,
        "kwh_delivered_today": float(kwh_today),
    }


@router.get("/oem-adapters")
async def all_oem_adapters(db: DB, _: CurrentUser = AdminRequired):
    from app.models.oem import OEMAdapter
    result = await db.execute(select(OEMAdapter))
    adapters = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "org_id": str(a.org_id),
            "name": a.name,
            "oem_slug": a.oem_slug,
            "connection_status": a.connection_status,
            "last_telemetry_at": a.last_telemetry_at.isoformat() if a.last_telemetry_at else None,
        }
        for a in adapters
    ]
