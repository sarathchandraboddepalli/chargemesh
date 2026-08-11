"""
Tests for the OCPP 1.6 state machine.
Validates connector state transitions and transaction authorization.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.network import ChargingNetwork, ChargingStation
from app.ocpp.charge_point import CONNECTOR_STATES


@pytest.mark.asyncio
async def test_boot_notification_marks_station_operational(db_session, test_org):
    """BootNotification should mark the station as operational."""
    from app.integrations.networks.ocpp_handler import handle_boot_notification

    network = ChargingNetwork(
        org_id=test_org.id,
        name="Test OCPP Network",
        network_slug="test_ocpp",
        integration_type="ocpp_1_6",
    )
    db_session.add(network)
    station = ChargingStation(
        network_id=network.id if network.id else uuid.uuid4(),  # will be set after flush
        external_station_id="OCPP-001",
        name="Test Station",
        is_operational=False,
        total_connectors=2,
        available_connectors=0,
        latitude=Decimal("18.9220"),
        longitude=Decimal("72.8347"),
    )
    db_session.add(network)
    await db_session.flush()
    station.network_id = network.id
    db_session.add(station)
    await db_session.flush()

    response = await handle_boot_notification(
        db=db_session,
        station_id=station.id,
        charge_point_vendor="ABB",
        charge_point_model="Terra AC W22",
        charge_point_serial_number="SN123456",
    )

    assert response["status"] == "Accepted"
    # Reload station
    from sqlalchemy import select
    result = await db_session.execute(select(ChargingStation).where(ChargingStation.id == station.id))
    updated = result.scalar_one()
    assert updated.is_operational == True


@pytest.mark.asyncio
async def test_start_transaction_updates_session(db_session, test_org):
    """StartTransaction should create an active session and decrement available connectors."""
    from app.integrations.networks.ocpp_handler import handle_start_transaction

    network = ChargingNetwork(
        org_id=test_org.id,
        name="Net2",
        network_slug="net2",
        integration_type="ocpp_1_6",
    )
    db_session.add(network)
    await db_session.flush()

    station = ChargingStation(
        network_id=network.id,
        external_station_id="ST-002",
        name="Station 2",
        is_operational=True,
        total_connectors=2,
        available_connectors=2,
        latitude=Decimal("18.9220"),
        longitude=Decimal("72.8347"),
    )
    db_session.add(station)
    await db_session.flush()

    now = datetime.now(timezone.utc)
    response = await handle_start_transaction(
        db=db_session,
        station_id=station.id,
        connector_id=1,
        id_tag="DRIVER-001",
        meter_start=0,
        timestamp=now,
    )

    assert response["idTagInfo"]["status"] == "Accepted"
    assert response["transactionId"] > 0

    # Verify available connectors decremented
    from sqlalchemy import select
    result = await db_session.execute(select(ChargingStation).where(ChargingStation.id == station.id))
    updated = result.scalar_one()
    assert updated.available_connectors == 1


@pytest.mark.asyncio
async def test_stop_transaction_completes_session(db_session, test_org):
    """StopTransaction should mark session as completed."""
    from app.integrations.networks.ocpp_handler import handle_start_transaction, handle_stop_transaction

    network = ChargingNetwork(
        org_id=test_org.id,
        name="Net3",
        network_slug="net3",
        integration_type="ocpp_1_6",
    )
    db_session.add(network)
    await db_session.flush()

    station = ChargingStation(
        network_id=network.id,
        external_station_id="ST-003",
        name="Station 3",
        is_operational=True,
        total_connectors=2,
        available_connectors=2,
        latitude=Decimal("18.9220"),
        longitude=Decimal("72.8347"),
    )
    db_session.add(station)
    await db_session.flush()

    start_time = datetime(2026, 8, 7, 10, 0, 0, tzinfo=timezone.utc)
    stop_time = datetime(2026, 8, 7, 11, 30, 0, tzinfo=timezone.utc)

    start_response = await handle_start_transaction(
        db=db_session,
        station_id=station.id,
        connector_id=1,
        id_tag="DRV-002",
        meter_start=0,
        timestamp=start_time,
    )
    txn_id = start_response["transactionId"]

    stop_response = await handle_stop_transaction(
        db=db_session,
        station_id=station.id,
        transaction_id=txn_id,
        id_tag="DRV-002",
        meter_stop=15000,  # 15 kWh in Wh
        timestamp=stop_time,
        reason="Local",
    )

    assert stop_response["idTagInfo"]["status"] == "Accepted"

    # Verify session is completed
    from sqlalchemy import select
    from app.models.session import ChargingSession
    result = await db_session.execute(
        select(ChargingSession).where(ChargingSession.external_session_id == str(txn_id))
    )
    session = result.scalar_one_or_none()
    assert session is not None
    assert session.status == "completed"
    assert session.duration_minutes == 90  # 1.5 hours
