"""
ChargeMesh — Settlement Service
BaaS settlement calculation: kWh cost + degradation cost.

Formula:
  kwh_cost = kwh_consumed × price_per_kwh_inr
  excess_degradation = max(0, actual_degradation - (threshold_pct × kwh_consumed / 100))
  degradation_cost = excess_degradation × price_per_soh_point_inr
  total = kwh_cost + degradation_cost

The degradation_threshold_pct represents the normal degradation rate per 100 kWh.
Anything above this threshold triggers the additional SoH-based surcharge.
This protects BaaS vendors from abnormal battery abuse by fleet operators.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.battery import Battery, BatterySwap
from app.models.ledger import BaaSPricingConfig, SettlementReport
from app.models.org import Organization


async def calculate_swap_settlement(
    db: AsyncSession,
    battery: Battery,
    fleet_org_id: uuid.UUID,
    kwh_consumed: float,
) -> dict:
    """
    Calculate settlement amounts for a single swap event.

    Args:
        battery: The battery being removed
        fleet_org_id: Fleet operator who used this battery
        kwh_consumed: kWh consumed since last swap

    Returns:
        dict with degradation_this_session and settlement_amount_inr
    """
    if kwh_consumed <= 0:
        return {"degradation_this_session": 0.0, "settlement_amount_inr": 0.0}

    # Get active pricing config for this fleet/vendor pair
    pricing = await _get_active_pricing(db, fleet_org_id, battery.owner_org_id, battery.model)
    if not pricing:
        print(
            f"[ChargeMesh] [SETTLEMENT] No pricing config for fleet={fleet_org_id} "
            f"vendor={battery.owner_org_id} model={battery.model} — settlement_amount=0"
        )
        return {"degradation_this_session": 0.0, "settlement_amount_inr": 0.0}

    price_per_kwh = float(pricing.price_per_kwh_inr)
    price_per_soh = float(pricing.price_per_soh_point_inr)
    threshold_pct = float(pricing.degradation_threshold_pct)

    # Calculate kWh cost
    kwh_cost = kwh_consumed * price_per_kwh

    # Estimate degradation from thermal stress (simplified linear model)
    # Full degradation model is in utils/battery_model.py
    from app.utils.battery_model import estimate_degradation_from_kwh
    actual_degradation = estimate_degradation_from_kwh(
        kwh_consumed=kwh_consumed,
        thermal_stress=float(battery.accumulated_thermal_stress or 0),
        cycle_count=battery.cycle_count or 0,
    )

    # Excess degradation = above what is expected for normal operation
    expected_degradation = threshold_pct * kwh_consumed / 100
    excess_degradation = max(0.0, actual_degradation - expected_degradation)
    degradation_cost = excess_degradation * price_per_soh

    total = kwh_cost + degradation_cost

    print(
        f"[ChargeMesh] [SETTLEMENT] Battery {battery.id} "
        f"kWh={kwh_consumed:.3f} "
        f"kwh_cost=₹{kwh_cost:.2f} "
        f"actual_deg={actual_degradation:.4f}% "
        f"excess_deg={excess_degradation:.4f}% "
        f"deg_cost=₹{degradation_cost:.2f} "
        f"total=₹{total:.2f}"
    )

    return {
        "degradation_this_session": round(actual_degradation, 4),
        "settlement_amount_inr": round(total, 2),
    }


async def generate_settlement_report(
    db: AsyncSession,
    fleet_org_id: uuid.UUID,
    baas_vendor_org_id: uuid.UUID,
    billing_period: str,  # "2026-07"
) -> Optional[SettlementReport]:
    """
    Generate a monthly settlement report for a fleet/vendor pair.
    Processes all pending battery_swaps for the billing period.
    Updates swap.settlement_status to 'included_in_report'.
    """
    # Parse billing period
    year, month = map(int, billing_period.split("-"))
    period_start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        period_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        period_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    # Get pending swaps for this period matching the vendor's batteries
    result = await db.execute(
        select(BatterySwap).where(
            BatterySwap.baas_vendor_org_id == baas_vendor_org_id,
            BatterySwap.settlement_status == "pending",
            BatterySwap.swapped_at >= period_start,
            BatterySwap.swapped_at < period_end,
        )
    )
    swaps = result.scalars().all()

    if not swaps:
        print(
            f"[ChargeMesh] [SETTLEMENT] No pending swaps for "
            f"fleet={fleet_org_id} vendor={baas_vendor_org_id} period={billing_period}"
        )
        return None

    pricing = await _get_active_pricing(db, fleet_org_id, baas_vendor_org_id, None)
    price_per_kwh = float(pricing.price_per_kwh_inr) if pricing else 8.0
    price_per_soh = float(pricing.price_per_soh_point_inr) if pricing else 0.0
    threshold_pct = float(pricing.degradation_threshold_pct) if pricing else 0.5

    total_swaps = 0
    total_kwh = 0.0
    total_kwh_cost = 0.0
    total_deg_cost = 0.0

    for swap in swaps:
        kwh = float(swap.kwh_consumed_this_session or 0)
        deg = float(swap.degradation_this_session or 0)
        expected_deg = threshold_pct * kwh / 100
        excess = max(0.0, deg - expected_deg)

        kwh_cost = kwh * price_per_kwh
        deg_cost = excess * price_per_soh
        swap_total = kwh_cost + deg_cost

        total_swaps += 1
        total_kwh += kwh
        total_kwh_cost += kwh_cost
        total_deg_cost += deg_cost

        # Mark as included
        swap.settlement_status = "included_in_report"
        db.add(swap)

    report = SettlementReport(
        fleet_org_id=fleet_org_id,
        baas_vendor_org_id=baas_vendor_org_id,
        billing_period=billing_period,
        total_swaps=total_swaps,
        total_kwh_consumed=round(total_kwh, 3),
        total_kwh_cost_inr=round(total_kwh_cost, 2),
        total_degradation_cost_inr=round(total_deg_cost, 2),
        total_amount_inr=round(total_kwh_cost + total_deg_cost, 2),
        status="draft",
    )
    db.add(report)
    await db.flush()

    print(
        f"[ChargeMesh] [SETTLEMENT] Report generated: {billing_period} "
        f"vendor={baas_vendor_org_id} swaps={total_swaps} "
        f"kWh={total_kwh:.1f} total=₹{report.total_amount_inr:.2f}"
    )
    return report


async def _get_active_pricing(
    db: AsyncSession,
    fleet_org_id: uuid.UUID,
    baas_vendor_org_id: uuid.UUID,
    battery_model: Optional[str],
) -> Optional[BaaSPricingConfig]:
    from datetime import date
    today = date.today()
    q = select(BaaSPricingConfig).where(
        BaaSPricingConfig.fleet_org_id == fleet_org_id,
        BaaSPricingConfig.baas_vendor_org_id == baas_vendor_org_id,
        BaaSPricingConfig.is_active == True,
        BaaSPricingConfig.effective_from <= today,
        (BaaSPricingConfig.effective_to.is_(None) | (BaaSPricingConfig.effective_to >= today)),
    )
    if battery_model:
        q = q.where(
            (BaaSPricingConfig.battery_model == battery_model) |
            (BaaSPricingConfig.battery_model.is_(None))
        )
    q = q.order_by(BaaSPricingConfig.effective_from.desc()).limit(1)
    result = await db.execute(q)
    return result.scalar_one_or_none()
