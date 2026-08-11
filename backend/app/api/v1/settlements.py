"""ChargeMesh — Settlement Report API Routes"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentOrg, CurrentUser, DB
from app.models.ledger import SettlementReport
from app.schemas.ledger import SettlementGenerateRequest, SettlementOut

router = APIRouter()


@router.post("/generate", response_model=list[SettlementOut], status_code=status.HTTP_202_ACCEPTED)
async def generate_settlements(payload: SettlementGenerateRequest, current_org: CurrentOrg, db: DB):
    """Generate settlement reports for a billing period. Queues background task."""
    from app.tasks.settlement_tasks import generate_monthly_settlements
    generate_monthly_settlements.delay(
        payload.billing_period,
        str(current_org.id),
        str(payload.baas_vendor_org_id) if payload.baas_vendor_org_id else None,
    )
    return []


@router.get("", response_model=list[SettlementOut])
async def list_settlements(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(SettlementReport).where(SettlementReport.fleet_org_id == current_org.id)
        .order_by(SettlementReport.generated_at.desc())
    )
    return result.scalars().all()


@router.get("/{settlement_id}", response_model=SettlementOut)
async def get_settlement(settlement_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(SettlementReport).where(
            SettlementReport.id == settlement_id,
            SettlementReport.fleet_org_id == current_org.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Settlement report not found")
    return report


@router.post("/{settlement_id}/approve", response_model=SettlementOut)
async def approve_settlement(
    settlement_id: uuid.UUID,
    current_user: CurrentUser,
    current_org: CurrentOrg,
    db: DB,
):
    result = await db.execute(
        select(SettlementReport).where(
            SettlementReport.id == settlement_id,
            SettlementReport.fleet_org_id == current_org.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Settlement report not found")
    if report.status != "draft":
        raise HTTPException(status_code=409, detail=f"Report is already {report.status}")

    report.status = "approved"
    report.approved_at = datetime.now(timezone.utc)
    report.approved_by = current_user.id
    db.add(report)

    # Notify BaaS vendor (queued)
    from app.tasks.notification_tasks import notify_settlement_approved
    notify_settlement_approved.delay(str(settlement_id))

    return report
