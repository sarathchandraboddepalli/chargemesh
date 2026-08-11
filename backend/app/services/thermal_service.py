"""
ChargeMesh — Thermal Service
Thermal stress index calculation and alert generation.

Thermal Stress Index Formula:
  For each telemetry interval:
    stress += max(0, battery_temp_celsius - 35.0) × duration_hours

  This gives cumulative degree-hours above the thermal comfort threshold (35°C).
  The 35°C baseline is derived from LFP/NMC battery literature for Indian climate conditions.

  Example: A battery at 46°C for 0.5 hours contributes (46-35) × 0.5 = 5.5 degree-hours.
  A stress score > 200 degree-hours indicates high degradation risk.

Thresholds:
  > 42°C → warning alert (high_temp)
  > 48°C → critical alert (rapid_temp_rise) + push notification
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.battery import Battery
from app.models.thermal import ThermalAlert
from app.models.vehicle import Vehicle


# Thermal comfort baseline (°C above which stress accumulates)
THERMAL_BASELINE_CELSIUS = 35.0


def calculate_thermal_stress_increment(
    battery_temp_celsius: float,
    duration_hours: float,
) -> float:
    """
    Calculate thermal stress increment for one telemetry interval.

    Formula: max(0, battery_temp - 35°C) × duration_hours

    Args:
        battery_temp_celsius: Battery temperature reading
        duration_hours: Duration of this interval in hours

    Returns:
        Thermal stress increment in degree-hours
    """
    return max(0.0, battery_temp_celsius - THERMAL_BASELINE_CELSIUS) * duration_hours


async def run_thermal_check(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    battery_id: Optional[uuid.UUID],
    battery_temp_celsius: float,
    ambient_temp_celsius: Optional[float],
    recorded_at: datetime,
    org_id: uuid.UUID,
    interval_minutes: float = 1.0,
) -> Optional[ThermalAlert]:
    """
    Check telemetry for thermal events and update battery stress index.

    Args:
        vehicle_id: Vehicle that sent this telemetry
        battery_id: Battery currently installed (from telemetry)
        battery_temp_celsius: Battery temperature at this reading
        ambient_temp_celsius: Ambient temperature (affects thermal model, optional)
        recorded_at: Telemetry timestamp
        org_id: Fleet org (for alert scoping)
        interval_minutes: Time since last telemetry reading (default 1 min)

    Returns:
        ThermalAlert if threshold exceeded, else None
    """
    duration_hours = interval_minutes / 60.0
    stress_increment = calculate_thermal_stress_increment(battery_temp_celsius, duration_hours)

    # Update battery accumulated thermal stress
    if battery_id:
        battery_result = await db.execute(select(Battery).where(Battery.id == battery_id))
        battery = battery_result.scalar_one_or_none()
        if battery:
            current_stress = float(battery.accumulated_thermal_stress or 0)
            battery.accumulated_thermal_stress = current_stress + stress_increment

            # Flag battery if stress score is critically high
            if float(battery.accumulated_thermal_stress) > 200:
                battery.is_flagged = True
                battery.flag_reason = (
                    f"Accumulated thermal stress {battery.accumulated_thermal_stress:.1f} "
                    f"degree-hours exceeds safe limit (200)"
                )
            db.add(battery)

    # Alert generation
    alert = None

    if battery_temp_celsius >= settings.THERMAL_CRITICAL_THRESHOLD:
        # Critical: > 48°C — create alert + push notification
        alert = ThermalAlert(
            org_id=org_id,
            battery_id=battery_id,
            vehicle_id=vehicle_id,
            alert_type="rapid_temp_rise",
            severity="critical",
            temperature_celsius=battery_temp_celsius,
            threshold_celsius=settings.THERMAL_CRITICAL_THRESHOLD,
            message=(
                f"CRITICAL: Battery temperature {battery_temp_celsius:.1f}°C exceeds critical threshold "
                f"{settings.THERMAL_CRITICAL_THRESHOLD}°C. Stop fast-charging immediately."
            ),
        )
        db.add(alert)
        await db.flush()

        # Queue push notification
        from app.tasks.notification_tasks import push_thermal_alert
        push_thermal_alert.delay(str(alert.id), "critical")

        print(
            f"[ChargeMesh] [THERMAL] CRITICAL alert for vehicle {vehicle_id}: "
            f"temp={battery_temp_celsius:.1f}°C (threshold={settings.THERMAL_CRITICAL_THRESHOLD}°C)"
        )

    elif battery_temp_celsius >= settings.THERMAL_WARNING_THRESHOLD:
        # Warning: > 42°C — check if we already have an unresolved alert
        existing_result = await db.execute(
            select(ThermalAlert).where(
                ThermalAlert.vehicle_id == vehicle_id,
                ThermalAlert.severity == "warning",
                ThermalAlert.is_resolved == False,
                ThermalAlert.created_at >= recorded_at - timedelta(hours=2),
            ).limit(1)
        )
        if not existing_result.scalar_one_or_none():
            alert = ThermalAlert(
                org_id=org_id,
                battery_id=battery_id,
                vehicle_id=vehicle_id,
                alert_type="high_temp",
                severity="warning",
                temperature_celsius=battery_temp_celsius,
                threshold_celsius=settings.THERMAL_WARNING_THRESHOLD,
                message=(
                    f"Battery temperature {battery_temp_celsius:.1f}°C exceeded warning threshold "
                    f"{settings.THERMAL_WARNING_THRESHOLD}°C. Monitor closely."
                ),
            )
            db.add(alert)
            await db.flush()
            print(
                f"[ChargeMesh] [THERMAL] WARNING alert for vehicle {vehicle_id}: "
                f"temp={battery_temp_celsius:.1f}°C (threshold={settings.THERMAL_WARNING_THRESHOLD}°C)"
            )

    return alert


async def check_sustained_alerts(db: AsyncSession):
    """
    Check for batteries sustaining high temperatures for extended periods.
    Run every 10 minutes by Celery Beat.
    Creates 'sustained_high_temp' alerts for batteries that have been above
    warning threshold for > 30 minutes without resolution.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    result = await db.execute(
        select(ThermalAlert).where(
            ThermalAlert.severity == "warning",
            ThermalAlert.is_resolved == False,
            ThermalAlert.alert_type == "high_temp",
            ThermalAlert.created_at <= cutoff,
        )
    )
    old_warnings = result.scalars().all()

    for alert in old_warnings:
        sustained = ThermalAlert(
            org_id=alert.org_id,
            battery_id=alert.battery_id,
            vehicle_id=alert.vehicle_id,
            alert_type="sustained_high_temp",
            severity="warning",
            temperature_celsius=alert.temperature_celsius,
            threshold_celsius=alert.threshold_celsius,
            message=(
                f"Battery has sustained high temperature for >30 minutes. "
                f"Original alert: {alert.created_at.isoformat()}"
            ),
        )
        db.add(sustained)
        # Mark original as resolved
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        db.add(alert)

    if old_warnings:
        await db.flush()
        print(f"[ChargeMesh] [THERMAL] Promoted {len(old_warnings)} sustained thermal alerts")
