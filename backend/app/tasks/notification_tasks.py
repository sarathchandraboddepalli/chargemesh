"""ChargeMesh — Notification Celery Tasks"""

import asyncio
import uuid

from app.worker import celery_app


@celery_app.task(name="app.tasks.notification_tasks.push_thermal_alert", queue="notifications")
def push_thermal_alert(alert_id_str: str, severity: str):
    """Send push notification for a thermal alert."""
    asyncio.run(_push_thermal(alert_id_str, severity))


@celery_app.task(name="app.tasks.notification_tasks.notify_settlement_approved", queue="notifications")
def notify_settlement_approved(settlement_id_str: str):
    """Notify BaaS vendor that a settlement has been approved."""
    asyncio.run(_notify_settlement(settlement_id_str))


async def _push_thermal(alert_id_str: str, severity: str):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.thermal import ThermalAlert
    from app.models.vehicle import Driver
    from app.services.notification_service import notify_thermal_alert

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ThermalAlert).where(ThermalAlert.id == uuid.UUID(alert_id_str)))
        alert = result.scalar_one_or_none()
        if not alert or not alert.vehicle_id:
            return

        # Find driver assigned to this vehicle
        driver_result = await db.execute(
            select(Driver).where(Driver.assigned_vehicle_id == alert.vehicle_id, Driver.is_active == True)
        )
        driver = driver_result.scalar_one_or_none()

        if driver and driver.user_id:
            # In production: look up driver's FCM token from a device_tokens table
            mock_token = f"mock_fcm_token_{driver.user_id}"
            notify_thermal_alert(
                driver_device_token=mock_token,
                severity=severity,
                temperature_celsius=float(alert.temperature_celsius or 0),
            )
        else:
            print(f"[ChargeMesh] [NOTIFICATION TASK] No driver found for thermal alert {alert_id_str}")


async def _notify_settlement(settlement_id_str: str):
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.ledger import SettlementReport
    from app.models.org import Organization
    from app.services.notification_service import send_email

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(SettlementReport).where(SettlementReport.id == uuid.UUID(settlement_id_str))
        )
        report = result.scalar_one_or_none()
        if not report:
            return

        vendor_result = await db.execute(
            select(Organization).where(Organization.id == report.baas_vendor_org_id)
        )
        vendor = vendor_result.scalar_one_or_none()
        vendor_name = vendor.name if vendor else "BaaS Vendor"

        send_email(
            to_email=f"settlements@{vendor_name.lower().replace(' ', '')}.in",
            subject=f"ChargeMesh Settlement Approved: {report.billing_period}",
            body_text=(
                f"Settlement report for {report.billing_period} has been approved.\n"
                f"Total amount: ₹{report.total_amount_inr:,.2f}\n"
                f"Total kWh: {report.total_kwh_consumed:.1f} kWh\n"
                f"Total swaps: {report.total_swaps}"
            ),
        )
