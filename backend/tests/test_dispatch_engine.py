"""
Tests for the dispatch engine (charge-to-complete calculation).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.vehicle import Vehicle
from app.models.telemetry import VehicleTelemetry


@pytest.mark.asyncio
async def test_dispatch_triggered_below_threshold(db_session, test_org):
    """Dispatch recommendation should be created when SoC < 25%."""
    from app.services.dispatch_service import evaluate_vehicle_dispatch

    vehicle = Vehicle(
        org_id=test_org.id,
        registration_number=f"MH{uuid.uuid4().hex[:6].upper()}",
        model_name="Ola S1 Pro",
        max_range_km=Decimal("181.0"),
    )
    db_session.add(vehicle)
    await db_session.flush()

    # Telemetry with critically low SoC (the MH02AB1234 scenario)
    telemetry = VehicleTelemetry(
        vehicle_id=vehicle.id,
        recorded_at=datetime.now(timezone.utc),
        state_of_charge=Decimal("18.0"),  # below 25% threshold
        estimated_range_km=Decimal("32.0"),
        latitude=Decimal("18.9220"),
        longitude=Decimal("72.8347"),
        is_charging=False,
    )
    db_session.add(telemetry)
    await db_session.flush()

    # remaining_delivery_km = 45 km (3 deliveries × 15 km avg)
    recommendation = await evaluate_vehicle_dispatch(
        db=db_session,
        vehicle=vehicle,
        latest_telemetry=telemetry,
        remaining_delivery_km=45.0,
    )

    assert recommendation is not None, (
        "Expected dispatch recommendation for vehicle at 18% SoC with 45km deliveries remaining"
    )
    assert float(recommendation.trigger_soc) == 18.0


@pytest.mark.asyncio
async def test_no_dispatch_above_threshold(db_session, test_org):
    """No dispatch recommendation when SoC >= 25%."""
    from app.services.dispatch_service import evaluate_vehicle_dispatch

    vehicle = Vehicle(
        org_id=test_org.id,
        registration_number=f"KA{uuid.uuid4().hex[:6].upper()}",
        model_name="Ather 450X",
        max_range_km=Decimal("146.0"),
    )
    db_session.add(vehicle)
    await db_session.flush()

    telemetry = VehicleTelemetry(
        vehicle_id=vehicle.id,
        recorded_at=datetime.now(timezone.utc),
        state_of_charge=Decimal("65.0"),  # healthy SoC
        estimated_range_km=Decimal("95.0"),
        is_charging=False,
    )
    db_session.add(telemetry)
    await db_session.flush()

    recommendation = await evaluate_vehicle_dispatch(
        db=db_session,
        vehicle=vehicle,
        latest_telemetry=telemetry,
        remaining_delivery_km=20.0,
    )

    assert recommendation is None, f"Unexpected dispatch at 65% SoC: {recommendation}"


@pytest.mark.asyncio
async def test_dispatch_finds_nearest_station(db_session, test_org):
    """Dispatch should select the nearest available station."""
    from app.services.dispatch_service import find_nearest_available_station
    from app.models.network import ChargingNetwork, ChargingStation

    network = ChargingNetwork(
        org_id=test_org.id,
        name="Test Network",
        network_slug="test",
        integration_type="ocpp_1_6",
    )
    db_session.add(network)
    await db_session.flush()

    # Station 5km away
    near_station = ChargingStation(
        network_id=network.id,
        external_station_id="NEAR-001",
        name="Near Station",
        latitude=Decimal("18.9320"),
        longitude=Decimal("72.8400"),
        available_connectors=2,
        total_connectors=2,
        is_operational=True,
    )
    # Station 20km away
    far_station = ChargingStation(
        network_id=network.id,
        external_station_id="FAR-001",
        name="Far Station",
        latitude=Decimal("19.1000"),
        longitude=Decimal("72.9000"),
        available_connectors=2,
        total_connectors=2,
        is_operational=True,
    )
    db_session.add(near_station)
    db_session.add(far_station)
    await db_session.flush()

    result = await find_nearest_available_station(
        db=db_session,
        latitude=18.9220,
        longitude=72.8347,
    )

    assert result is not None
    assert result.external_station_id == "NEAR-001", f"Expected NEAR-001, got {result.external_station_id}"
