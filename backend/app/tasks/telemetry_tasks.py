"""
ChargeMesh — Telemetry Celery Tasks
Polls OEM adapters and processes telemetry batches.

Pipeline:
  poll_all_oem_adapters (every 2 min)
    → fetch from OEM adapter
    → process_telemetry_batch
      → upsert vehicle_telemetry (ON CONFLICT DO NOTHING)
      → run_thermal_check
      → run_dispatch_evaluation
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone

from app.worker import celery_app


@celery_app.task(name="app.tasks.telemetry_tasks.poll_all_oem_adapters", queue="telemetry")
def poll_all_oem_adapters():
    """Celery Beat task: poll all active OEM adapters for telemetry every 2 minutes."""
    asyncio.run(_poll_all_oem_adapters())


async def _poll_all_oem_adapters():
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.oem import OEMAdapter

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(OEMAdapter).where(OEMAdapter.is_active == True))
        adapters = result.scalars().all()

    for adapter in adapters:
        print(f"[ChargeMesh] [TELEMETRY TASK] Polling OEM adapter: {adapter.name} ({adapter.oem_slug})")
        try:
            from app.integrations.oem import get_oem_adapter
            oem = get_oem_adapter(
                oem_slug=adapter.oem_slug,
                adapter_id=adapter.id,
                config=adapter.config or {},
            )
            records = await oem.fetch_telemetry(vehicle_oem_ids=[])

            # Queue batch processing
            process_telemetry_batch.delay(
                str(adapter.id),
                [
                    {
                        "vehicle_id": str(r.vehicle_id),
                        "recorded_at": r.recorded_at.isoformat(),
                        "state_of_charge": r.state_of_charge,
                        "state_of_health": r.state_of_health,
                        "latitude": r.latitude,
                        "longitude": r.longitude,
                        "speed_kmh": r.speed_kmh,
                        "battery_temp_celsius": r.battery_temp_celsius,
                        "ambient_temp_celsius": r.ambient_temp_celsius,
                        "odometer_km": r.odometer_km,
                        "is_charging": r.is_charging,
                        "charging_power_kw": r.charging_power_kw,
                        "estimated_range_km": r.estimated_range_km,
                        "battery_id": r.battery_id,
                        "raw_data": r.raw_data,
                    }
                    for r in records
                ],
            )
        except Exception as e:
            print(f"[ChargeMesh] [TELEMETRY TASK] Error polling {adapter.name}: {e}")


@celery_app.task(name="app.tasks.telemetry_tasks.process_telemetry_batch", queue="telemetry")
def process_telemetry_batch(adapter_id_str: str, records: list[dict]):
    """
    Process a batch of telemetry records:
    1. Upsert into vehicle_telemetry (idempotent — ON CONFLICT DO NOTHING)
    2. Update vehicle status
    3. Run thermal check
    4. Run dispatch evaluation
    """
    asyncio.run(_process_batch(adapter_id_str, records))


async def _process_batch(adapter_id_str: str, records: list[dict]):
    from sqlalchemy import text
    from app.database import AsyncSessionLocal
    from app.services.telemetry_service import process_single_record

    async with AsyncSessionLocal() as db:
        for record in records:
            try:
                vehicle_id = record.get("vehicle_id")
                if not vehicle_id:
                    continue

                recorded_at = record.get("recorded_at")
                if isinstance(recorded_at, str):
                    from dateutil import parser
                    recorded_at_dt = parser.parse(recorded_at)
                else:
                    recorded_at_dt = recorded_at

                # Idempotent insert — ON CONFLICT DO NOTHING prevents duplicate writes
                # from retry logic or OEM adapter re-sends
                stmt = text("""
                    INSERT INTO vehicle_telemetry (
                        vehicle_id, recorded_at, state_of_charge, state_of_health,
                        latitude, longitude, speed_kmh, battery_temp_celsius,
                        ambient_temp_celsius, odometer_km, is_charging, charging_power_kw,
                        estimated_range_km, battery_id, raw_data
                    ) VALUES (
                        :vehicle_id, :recorded_at, :state_of_charge, :state_of_health,
                        :latitude, :longitude, :speed_kmh, :battery_temp_celsius,
                        :ambient_temp_celsius, :odometer_km, :is_charging, :charging_power_kw,
                        :estimated_range_km, :battery_id, :raw_data
                    ) ON CONFLICT (vehicle_id, recorded_at) DO NOTHING
                """)
                await db.execute(stmt, {
                    "vehicle_id": uuid.UUID(vehicle_id),
                    "recorded_at": recorded_at_dt,
                    "state_of_charge": record.get("state_of_charge"),
                    "state_of_health": record.get("state_of_health"),
                    "latitude": record.get("latitude"),
                    "longitude": record.get("longitude"),
                    "speed_kmh": record.get("speed_kmh"),
                    "battery_temp_celsius": record.get("battery_temp_celsius"),
                    "ambient_temp_celsius": record.get("ambient_temp_celsius"),
                    "odometer_km": record.get("odometer_km"),
                    "is_charging": record.get("is_charging", False),
                    "charging_power_kw": record.get("charging_power_kw"),
                    "estimated_range_km": record.get("estimated_range_km"),
                    "battery_id": uuid.UUID(record["battery_id"]) if record.get("battery_id") else None,
                    "raw_data": json.dumps(record.get("raw_data")) if record.get("raw_data") else None,
                })

                # Run downstream processing
                await process_single_record(db=db, record=record)

            except Exception as e:
                print(f"[ChargeMesh] [TELEMETRY TASK] Error processing record {record.get('vehicle_id')}: {e}")

        await db.commit()

    print(f"[ChargeMesh] [TELEMETRY TASK] Processed {len(records)} records from adapter {adapter_id_str}")
