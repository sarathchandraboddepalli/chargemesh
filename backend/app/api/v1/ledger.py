"""ChargeMesh — BaaS Ledger API Routes"""

import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentOrg, DB
from app.models.battery import BatterySwap
from app.models.ledger import BaaSPricingConfig, SettlementReport
from app.models.org import Organization
from app.schemas.ledger import LedgerSummary, PricingConfigCreate, PricingConfigOut

router = APIRouter()


@router.get("/summary", response_model=LedgerSummary)
async def ledger_summary(current_org: CurrentOrg, db: DB):
    # Sum pending swap settlement amounts for this fleet
    result = await db.execute(
        select(
            func.sum(BatterySwap.settlement_amount_inr),
            func.sum(BatterySwap.kwh_consumed_this_session),
        ).where(
            BatterySwap.settlement_status == "pending",
        )
    )
    row = result.one()
    total_pending = row[0] or Decimal("0")
    total_kwh = row[1] or Decimal("0")

    # Per-vendor breakdown
    vendor_result = await db.execute(
        select(
            BatterySwap.baas_vendor_org_id,
            func.sum(BatterySwap.settlement_amount_inr),
            func.sum(BatterySwap.kwh_consumed_this_session),
            func.count(BatterySwap.id),
        )
        .where(BatterySwap.settlement_status == "pending", BatterySwap.baas_vendor_org_id.isnot(None))
        .group_by(BatterySwap.baas_vendor_org_id)
    )
    vendors = []
    for vendor_id, amount, kwh, count in vendor_result.all():
        org_result = await db.execute(select(Organization).where(Organization.id == vendor_id))
        org = org_result.scalar_one_or_none()
        vendors.append({
            "vendor_id": str(vendor_id),
            "vendor_name": org.name if org else "Unknown",
            "pending_amount_inr": float(amount or 0),
            "kwh_consumed": float(kwh or 0),
            "swap_count": count,
        })

    return LedgerSummary(
        total_pending_amount_inr=total_pending,
        total_kwh_consumed=total_kwh,
        vendors=vendors,
    )


@router.get("/vendors/{vendor_id}")
async def vendor_ledger(vendor_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(BatterySwap)
        .where(
            BatterySwap.baas_vendor_org_id == vendor_id,
            BatterySwap.settlement_status == "pending",
        )
        .order_by(BatterySwap.swapped_at.desc())
    )
    swaps = result.scalars().all()
    total = sum(float(s.settlement_amount_inr or 0) for s in swaps)
    kwh = sum(float(s.kwh_consumed_this_session or 0) for s in swaps)
    return {"vendor_id": str(vendor_id), "pending_swaps": len(swaps), "total_amount_inr": total, "total_kwh": kwh}


@router.get("/batteries/{battery_id}")
async def battery_ledger(battery_id: uuid.UUID, current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(BatterySwap).where(
            (BatterySwap.removed_battery_id == battery_id) |
            (BatterySwap.installed_battery_id == battery_id)
        ).order_by(BatterySwap.swapped_at.desc())
    )
    swaps = result.scalars().all()
    total_kwh = sum(float(s.kwh_consumed_this_session or 0) for s in swaps)
    total_deg = sum(float(s.degradation_this_session or 0) for s in swaps)
    return {"battery_id": str(battery_id), "total_kwh_consumed": total_kwh, "total_degradation": total_deg, "swap_count": len(swaps)}


@router.get("/pricing-config", response_model=list[PricingConfigOut])
async def get_pricing_config(current_org: CurrentOrg, db: DB):
    result = await db.execute(
        select(BaaSPricingConfig).where(
            BaaSPricingConfig.fleet_org_id == current_org.id,
            BaaSPricingConfig.is_active == True,
        )
    )
    return result.scalars().all()


@router.put("/pricing-config", response_model=PricingConfigOut, status_code=status.HTTP_201_CREATED)
async def upsert_pricing_config(payload: PricingConfigCreate, current_org: CurrentOrg, db: DB):
    config = BaaSPricingConfig(
        fleet_org_id=current_org.id,
        **payload.model_dump(exclude_none=True),
    )
    db.add(config)
    await db.flush()
    return config
