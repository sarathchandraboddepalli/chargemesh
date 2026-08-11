"""
ChargeMesh — OCPP 1.6 ChargePoint Handler
Implements the Central System role for OCPP 1.6.

OCPP 1.6 State Machine (connector level):
  Available → Preparing → Charging → Finishing → Available
  Available → Unavailable (hardware fault)
  Any → Faulted

IMPORTANT: RemoteStartTransaction is only accepted when connector is in Available state.
"""

import uuid
from datetime import datetime, timezone

from ocpp.routing import on
from ocpp.v16 import ChargePoint as OcppChargePoint
from ocpp.v16 import call_result, datatypes
from ocpp.v16.enums import Action, AuthorizationStatus, RegistrationStatus

from app.database import AsyncSessionLocal
from app.integrations.networks.ocpp_handler import (
    handle_boot_notification,
    handle_heartbeat,
    handle_meter_values,
    handle_start_transaction,
    handle_status_notification,
    handle_stop_transaction,
)

# In-memory connector state per charge point
# {charge_point_id: {connector_id: "Available"|"Charging"|"Faulted"|...}}
CONNECTOR_STATES: dict[str, dict[int, str]] = {}


class ChargeMeshChargePoint(OcppChargePoint):
    """
    OCPP 1.6 Central System ChargePoint handler.
    Each connected charging station gets one instance of this class.
    """

    def __init__(self, id, connection, station_id: uuid.UUID, response_timeout=30):
        super().__init__(id, connection, response_timeout)
        self.station_id = station_id
        CONNECTOR_STATES[id] = {}

    def get_connector_state(self, connector_id: int) -> str:
        return CONNECTOR_STATES.get(self.id, {}).get(connector_id, "Unknown")

    def set_connector_state(self, connector_id: int, state: str):
        if self.id not in CONNECTOR_STATES:
            CONNECTOR_STATES[self.id] = {}
        CONNECTOR_STATES[self.id][connector_id] = state
        print(f"[ChargeMesh] [OCPP] {self.id} connector {connector_id} → {state}")

    @on(Action.boot_notification)
    async def on_boot_notification(
        self,
        charge_point_vendor: str,
        charge_point_model: str,
        **kwargs,
    ):
        async with AsyncSessionLocal() as db:
            response_data = await handle_boot_notification(
                db=db,
                station_id=self.station_id,
                charge_point_vendor=charge_point_vendor,
                charge_point_model=charge_point_model,
                charge_point_serial_number=kwargs.get("charge_point_serial_number"),
            )
            await db.commit()

        print(f"[ChargeMesh] [OCPP] BootNotification from {self.id} ({charge_point_vendor} {charge_point_model})")
        return call_result.BootNotification(
            current_time=response_data["currentTime"],
            interval=response_data["interval"],
            status=RegistrationStatus.accepted,
        )

    @on(Action.heartbeat)
    async def on_heartbeat(self, **kwargs):
        async with AsyncSessionLocal() as db:
            await handle_heartbeat(db=db, station_id=self.station_id)
            await db.commit()

        # Update the last-heartbeat timestamp so the heartbeat monitor uses
        # the actual latest heartbeat time, not the initial connection time.
        from app.ocpp.server import CONNECTED_CHARGE_POINTS
        if self.id in CONNECTED_CHARGE_POINTS:
            cp_obj, _ = CONNECTED_CHARGE_POINTS[self.id]
            CONNECTED_CHARGE_POINTS[self.id] = (cp_obj, datetime.now(timezone.utc))

        print(f"[ChargeMesh] [OCPP] Heartbeat from {self.id}")
        return call_result.Heartbeat(
            current_time=datetime.now(timezone.utc).isoformat()
        )

    @on(Action.status_notification)
    async def on_status_notification(
        self,
        connector_id: int,
        error_code: str,
        status: str,
        **kwargs,
    ):
        self.set_connector_state(connector_id, status)

        async with AsyncSessionLocal() as db:
            await handle_status_notification(
                db=db,
                station_id=self.station_id,
                connector_id=connector_id,
                status=status,
                error_code=error_code,
            )
            await db.commit()

        return call_result.StatusNotification()

    @on(Action.start_transaction)
    async def on_start_transaction(
        self,
        connector_id: int,
        id_tag: str,
        meter_start: int,
        timestamp: str,
        **kwargs,
    ):
        """
        Authorize and record transaction start.
        OCPP state machine: connector must be in Available or Preparing state.
        """
        connector_state = self.get_connector_state(connector_id)
        if connector_state not in ("Available", "Preparing", "Unknown"):
            print(
                f"[ChargeMesh] [OCPP] StartTransaction rejected: connector {connector_id} "
                f"is in {connector_state} state (must be Available)"
            )
            return call_result.StartTransaction(
                transaction_id=0,
                id_tag_info=datatypes.IdTagInfo(status=AuthorizationStatus.blocked),
            )

        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        async with AsyncSessionLocal() as db:
            response = await handle_start_transaction(
                db=db,
                station_id=self.station_id,
                connector_id=connector_id,
                id_tag=id_tag,
                meter_start=meter_start,
                timestamp=ts,
            )
            await db.commit()

        if response["idTagInfo"]["status"] == "Accepted":
            self.set_connector_state(connector_id, "Charging")

        print(
            f"[ChargeMesh] [OCPP] StartTransaction: {self.id} connector={connector_id} "
            f"id_tag={id_tag} txn_id={response['transactionId']}"
        )
        return call_result.StartTransaction(
            transaction_id=response["transactionId"],
            id_tag_info=datatypes.IdTagInfo(
                status=AuthorizationStatus(response["idTagInfo"]["status"])
            ),
        )

    @on(Action.stop_transaction)
    async def on_stop_transaction(
        self,
        meter_stop: int,
        timestamp: str,
        transaction_id: int,
        **kwargs,
    ):
        """Finalize transaction and update session records."""
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        async with AsyncSessionLocal() as db:
            response = await handle_stop_transaction(
                db=db,
                station_id=self.station_id,
                transaction_id=transaction_id,
                id_tag=kwargs.get("id_tag"),
                meter_stop=meter_stop,
                timestamp=ts,
                reason=kwargs.get("reason"),
            )
            await db.commit()

        # Reset connector state to Available
        for connector_id, state in CONNECTOR_STATES.get(self.id, {}).items():
            if state == "Charging":
                self.set_connector_state(connector_id, "Available")
                break

        print(
            f"[ChargeMesh] [OCPP] StopTransaction: {self.id} txn_id={transaction_id} "
            f"meter_stop={meter_stop}Wh reason={kwargs.get('reason', 'Local')}"
        )
        return call_result.StopTransaction(
            id_tag_info=datatypes.IdTagInfo(status=AuthorizationStatus.accepted)
        )

    @on(Action.meter_values)
    async def on_meter_values(
        self,
        connector_id: int,
        meter_value: list,
        **kwargs,
    ):
        """Process meter values during an active charging session."""
        transaction_id = kwargs.get("transaction_id")

        async with AsyncSessionLocal() as db:
            await handle_meter_values(
                db=db,
                station_id=self.station_id,
                transaction_id=transaction_id,
                meter_values=meter_value,
            )
            await db.commit()

        return call_result.MeterValues()
