"""
ChargeMesh — Settlement Celery Tasks
Monthly settlement generation runs on 1st of each month at 02:00 IST.
"""

import asyncio
import uuid
from typing import Optional

from app.worker import celery_app


@celery_app.task(name="app.tasks.settlement_tasks.generate_monthly_settlements", queue="settlements")
def generate_monthly_settlements(
    billing_period: str,
    fleet_org_id_str: Optional[str] = None,
    baas_vendor_org_id_str: Optional[str] = None,
):
    """
    Generate settlement reports for a billing period.
    Runs all fleet/vendor pairs with active pricing config.
    """
    asyncio.run(_generate(billing_period, fleet_org_id_str, baas_vendor_org_id_str))


async def _generate(billing_period: str, fleet_org_id_str: Optional[str], vendor_id_str: Optional[str]):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.ledger import BaaSPricingConfig
    from app.services.settlement_service import generate_settlement_report

    async with AsyncSessionLocal() as db:
        q = select(BaaSPricingConfig).where(BaaSPricingConfig.is_active == True)
        if fleet_org_id_str:
            q = q.where(BaaSPricingConfig.fleet_org_id == uuid.UUID(fleet_org_id_str))
        if vendor_id_str:
            q = q.where(BaaSPricingConfig.baas_vendor_org_id == uuid.UUID(vendor_id_str))

        result = await db.execute(q)
        configs = result.scalars().all()

        for config in configs:
            print(
                f"[ChargeMesh] [SETTLEMENT TASK] Generating report: "
                f"period={billing_period} fleet={config.fleet_org_id} vendor={config.baas_vendor_org_id}"
            )
            report = await generate_settlement_report(
                db=db,
                fleet_org_id=config.fleet_org_id,
                baas_vendor_org_id=config.baas_vendor_org_id,
                billing_period=billing_period,
            )
            if report:
                print(f"[ChargeMesh] [SETTLEMENT TASK] Report {report.id} generated: ₹{report.total_amount_inr}")

        await db.commit()
