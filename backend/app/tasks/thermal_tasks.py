"""ChargeMesh — Thermal Celery Tasks"""

import asyncio

from app.worker import celery_app


@celery_app.task(name="app.tasks.thermal_tasks.check_sustained_alerts", queue="dispatch")
def check_sustained_alerts():
    """Promote sustained thermal alerts (every 10 min via Celery Beat)."""
    asyncio.run(_check_sustained())


async def _check_sustained():
    from app.database import AsyncSessionLocal
    from app.services.thermal_service import check_sustained_alerts as _service_check
    async with AsyncSessionLocal() as db:
        await _service_check(db)
        await db.commit()
