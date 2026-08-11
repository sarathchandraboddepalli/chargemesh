"""ChargeMesh — Predictive Dispatch API Routes"""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentOrg, CurrentUser, DB
from app.config import settings
from app.models.dispatch import DispatchRecommendation
from app.models.vehicle import Vehicle
from app.schemas.dispatch import (
    DispatchConfigOut,
    DispatchConfigUpdate,
    DispatchOverride,
    DispatchRecommendationOut,
)

router = APIRouter()


@router.get("/recommendations", response_model=list[DispatchRecommendationOut])
async def get_recommendations(current_org: CurrentOrg, db: DB):
    """Get current active (unresolved) dispatch recommendations for all at-risk vehicles."""
    result = await db.execute(
        select(DispatchRecommendation)
        .where(
            DispatchRecommendation.org_id == current_org.id,
            DispatchRecommendation.was_acted_upon.is_(None),  # not yet acted upon or overridden
        )
        .order_by(DispatchRecommendation.recommended_at.desc())
        .limit(100)
    )
    recs = result.scalars().all()
    out = []
    for rec in recs:
        item = DispatchRecommendationOut.model_validate(rec)
        # Enrich with vehicle registration
        v_result = await db.execute(select(Vehicle).where(Vehicle.id == rec.vehicle_id))
        vehicle = v_result.scalar_one_or_none()
        if vehicle:
            item.vehicle_registration = vehicle.registration_number
        out.append(item)
    return out


@router.get("/vehicle/{vehicle_id}", response_model=DispatchRecommendationOut)
async def get_vehicle_recommendation(vehicle_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(DispatchRecommendation)
        .join(Vehicle, Vehicle.id == DispatchRecommendation.vehicle_id)
        .where(
            DispatchRecommendation.vehicle_id == vehicle_id,
            Vehicle.org_id == current_org.id,
            DispatchRecommendation.was_acted_upon.is_(None),
        )
        .order_by(DispatchRecommendation.recommended_at.desc())
        .limit(1)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="No active recommendation for this vehicle")
    return rec


@router.post("/vehicle/{vehicle_id}/override")
async def override_recommendation(
    vehicle_id: uuid.UUID,
    payload: DispatchOverride,
    current_user: CurrentUser,
    current_org: CurrentOrg,
    db: DB,
):
    result = await db.execute(
        select(DispatchRecommendation)
        .join(Vehicle, Vehicle.id == DispatchRecommendation.vehicle_id)
        .where(
            DispatchRecommendation.vehicle_id == vehicle_id,
            Vehicle.org_id == current_org.id,
            DispatchRecommendation.was_acted_upon.is_(None),
        )
        .order_by(DispatchRecommendation.recommended_at.desc())
        .limit(1)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="No active recommendation to override")

    rec.was_acted_upon = False
    rec.overridden_by = current_user.id
    rec.override_reason = payload.reason
    db.add(rec)
    return {"detail": "Recommendation overridden", "recommendation_id": str(rec.id)}


@router.get("/config", response_model=DispatchConfigOut)
async def get_dispatch_config(current_org: CurrentOrg):
    # In production, these would be org-level config stored in DB
    return DispatchConfigOut(
        soc_threshold=settings.DISPATCH_SOC_THRESHOLD,
        safety_buffer_km=settings.DISPATCH_SAFETY_BUFFER_KM,
    )


@router.put("/config", response_model=DispatchConfigOut)
async def update_dispatch_config(payload: DispatchConfigUpdate, current_org: CurrentOrg):
    # In production: persist to org config table
    # For MVP: return the updated values (runtime only)
    return DispatchConfigOut(
        soc_threshold=payload.soc_threshold or settings.DISPATCH_SOC_THRESHOLD,
        safety_buffer_km=payload.safety_buffer_km or settings.DISPATCH_SAFETY_BUFFER_KM,
    )
