"""ChargeMesh — Dispatch Celery Tasks"""

import asyncio
import uuid

from app.worker import celery_app


@celery_app.task(name="app.tasks.dispatch_tasks.run_dispatch_evaluation", queue="dispatch")
def run_dispatch_evaluation(vehicle_id_str: str, soc: float, estimated_range_km: float):
    """Evaluate a single vehicle for dispatch recommendation."""
    asyncio.run(_run_dispatch(vehicle_id_str, soc, estimated_range_km))


async def _run_dispatch(vehicle_id_str: str, soc: float, estimated_range_km: float):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.vehicle import Vehicle
    from app.models.telemetry import VehicleTelemetry
    from app.services.dispatch_service import evaluate_vehicle_dispatch

    async with AsyncSessionLocal() as db:
        v_result = await db.execute(select(Vehicle).where(Vehicle.id == uuid.UUID(vehicle_id_str)))
        vehicle = v_result.scalar_one_or_none()
        if not vehicle:
            return

        tel_result = await db.execute(
            select(VehicleTelemetry)
            .where(VehicleTelemetry.vehicle_id == vehicle.id)
            .order_by(VehicleTelemetry.recorded_at.desc())
            .limit(1)
        )
        telemetry = tel_result.scalar_one_or_none()
        if not telemetry:
            return

        await evaluate_vehicle_dispatch(db=db, vehicle=vehicle, latest_telemetry=telemetry)
        await db.commit()
