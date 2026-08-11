"""
Tests for BaaS settlement calculation.
Validates kWh cost + degradation cost formula.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.models.battery import Battery
from app.models.ledger import BaaSPricingConfig
from app.models.org import Organization


@pytest.mark.asyncio
async def test_settlement_sun_mobility_pricing(db_session, test_org):
    """
    Sun Mobility pricing: Rs.8/kWh + Rs.50/SoH point
    With 42 kWh consumed and moderate thermal stress.
    """
    from app.services.settlement_service import calculate_swap_settlement

    # Create Sun Mobility vendor org
    vendor_org = Organization(name="Sun Mobility", org_type="baas_vendor")
    db_session.add(vendor_org)
    await db_session.flush()

    # Pricing config: Rs.8/kWh + Rs.50/SoH point
    pricing = BaaSPricingConfig(
        fleet_org_id=test_org.id,
        baas_vendor_org_id=vendor_org.id,
        price_per_kwh_inr=Decimal("8.0"),
        price_per_soh_point_inr=Decimal("50.0"),
        degradation_threshold_pct=Decimal("0.5"),
        effective_from=date(2026, 1, 1),
        is_active=True,
    )
    db_session.add(pricing)

    battery = Battery(
        owner_org_id=vendor_org.id,
        model="Sun_3kWh_LFP",
        nominal_capacity_kwh=Decimal("3.0"),
        current_soh=Decimal("94.0"),
        cycle_count=120,
        accumulated_thermal_stress=Decimal("45.0"),
    )
    db_session.add(battery)
    await db_session.flush()

    result = await calculate_swap_settlement(
        db=db_session,
        battery=battery,
        fleet_org_id=test_org.id,
        kwh_consumed=42.0,  # Mock: MH02CD9012 scenario — 42 kWh consumed
    )

    assert result is not None
    kwh_cost = 42.0 * 8.0  # = 336 INR
    assert result["settlement_amount_inr"] >= kwh_cost, (
        f"Settlement ₹{result['settlement_amount_inr']} should be >= kWh cost ₹{kwh_cost}"
    )
    print(f"Sun Mobility settlement: ₹{result['settlement_amount_inr']:.2f} for 42 kWh")


@pytest.mark.asyncio
async def test_settlement_no_excess_degradation(db_session, test_org):
    """When degradation is within threshold, no SoH surcharge applies."""
    from app.services.settlement_service import calculate_swap_settlement

    vendor_org = Organization(name="Local BaaS Co.", org_type="baas_vendor")
    db_session.add(vendor_org)
    await db_session.flush()

    # Rs.9/kWh, no SoH surcharge
    pricing = BaaSPricingConfig(
        fleet_org_id=test_org.id,
        baas_vendor_org_id=vendor_org.id,
        price_per_kwh_inr=Decimal("9.0"),
        price_per_soh_point_inr=Decimal("0"),  # no SoH surcharge
        degradation_threshold_pct=Decimal("0.5"),
        effective_from=date(2026, 1, 1),
        is_active=True,
    )
    db_session.add(pricing)

    battery = Battery(
        owner_org_id=vendor_org.id,
        model="Local_3kWh",
        nominal_capacity_kwh=Decimal("3.0"),
        current_soh=Decimal("95.0"),
        cycle_count=50,
        accumulated_thermal_stress=Decimal("5.0"),  # low thermal stress
    )
    db_session.add(battery)
    await db_session.flush()

    result = await calculate_swap_settlement(
        db=db_session,
        battery=battery,
        fleet_org_id=test_org.id,
        kwh_consumed=10.0,
    )

    expected = 10.0 * 9.0  # = 90 INR
    # With no SoH surcharge, total should be close to kwh cost only
    assert abs(result["settlement_amount_inr"] - expected) < 5.0, (
        f"Expected ~₹{expected}, got ₹{result['settlement_amount_inr']}"
    )


@pytest.mark.asyncio
async def test_settlement_zero_kwh(db_session, test_org):
    """Zero kWh consumed should result in zero settlement."""
    from app.services.settlement_service import calculate_swap_settlement

    battery = Battery(
        owner_org_id=test_org.id,
        model="test",
        current_soh=Decimal("95.0"),
        cycle_count=10,
        accumulated_thermal_stress=Decimal("0"),
    )
    db_session.add(battery)
    await db_session.flush()

    result = await calculate_swap_settlement(
        db=db_session,
        battery=battery,
        fleet_org_id=test_org.id,
        kwh_consumed=0.0,
    )

    assert result["settlement_amount_inr"] == 0.0
    assert result["degradation_this_session"] == 0.0
