"""ChargeMesh — OEM Adapter Integration API"""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentOrg, DB
from app.models.oem import OEMAdapter

router = APIRouter()


@router.get("")
async def list_oems(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(OEMAdapter).where(OEMAdapter.org_id == current_org.id, OEMAdapter.is_active == True)
    )
    adapters = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "oem_slug": a.oem_slug,
            "connection_status": a.connection_status,
            "last_telemetry_at": a.last_telemetry_at.isoformat() if a.last_telemetry_at else None,
        }
        for a in adapters
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_oem(payload: dict, current_org: CurrentOrg, db: DB):
    adapter = OEMAdapter(
        org_id=current_org.id,
        name=payload["name"],
        oem_slug=payload["oem_slug"],
        base_url=payload.get("base_url"),
        config=payload.get("config"),
    )
    db.add(adapter)
    await db.flush()
    return {"id": str(adapter.id), "name": adapter.name}


@router.get("/{oem_id}/status")
async def oem_status(oem_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(OEMAdapter).where(OEMAdapter.id == oem_id, OEMAdapter.org_id == current_org.id)
    )
    adapter = result.scalar_one_or_none()
    if not adapter:
        raise HTTPException(status_code=404, detail="OEM adapter not found")
    return {
        "id": str(adapter.id),
        "name": adapter.name,
        "oem_slug": adapter.oem_slug,
        "connection_status": adapter.connection_status,
        "last_telemetry_at": adapter.last_telemetry_at.isoformat() if adapter.last_telemetry_at else None,
    }
