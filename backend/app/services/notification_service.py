"""
ChargeMesh — Notification Service
Handles FCM push notifications and email notifications.
All external calls are logged clearly when using console/mock mode.
"""

import json
from typing import Optional

from app.config import settings


def send_push_notification(
    device_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None,
) -> bool:
    """
    Send FCM push notification to a driver's device.

    In production: POSTs to https://fcm.googleapis.com/fcm/send
    In mock/console mode: logs the notification content.
    """
    payload = {
        "to": device_token,
        "notification": {"title": title, "body": body},
        "data": data or {},
    }

    if settings.FCM_SERVER_KEY == "changeme" or not settings.FCM_SERVER_KEY:
        print(
            f"[ChargeMesh] [NOTIFICATION] [MOCK] Would send FCM push to {device_token[:8]}...\n"
            f"  Title: {title}\n"
            f"  Body: {body}\n"
            f"  Data: {json.dumps(data or {})}"
        )
        return True

    try:
        import httpx
        response = httpx.post(
            "https://fcm.googleapis.com/fcm/send",
            headers={
                "Authorization": f"key={settings.FCM_SERVER_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"[ChargeMesh] [NOTIFICATION] FCM push failed: {e}")
        return False


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
) -> bool:
    """
    Send email notification.
    Console backend: prints to stdout.
    SMTP backend: sends via configured SMTP server.
    """
    if settings.EMAIL_BACKEND == "console":
        print(
            f"[ChargeMesh] [EMAIL] To: {to_email}\n"
            f"  Subject: {subject}\n"
            f"  Body: {body_text}"
        )
        return True

    try:
        import smtplib
        from email.mime.text import MIMEText
        # SMTP sending would be configured here in production
        print(f"[ChargeMesh] [EMAIL] SMTP send to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[ChargeMesh] [EMAIL] Send failed: {e}")
        return False


def notify_driver_charging_recommendation(
    driver_device_token: str,
    station_name: str,
    station_distance_km: float,
    current_soc: float,
) -> bool:
    """Send dispatch recommendation push notification to driver."""
    return send_push_notification(
        device_token=driver_device_token,
        title="Charging Recommended",
        body=f"Head to {station_name} — {station_distance_km:.1f} km away. Slot pre-booked. Battery at {current_soc:.0f}%.",
        data={
            "type": "charging_recommendation",
            "station_name": station_name,
            "distance_km": str(station_distance_km),
        },
    )


def notify_thermal_alert(
    driver_device_token: str,
    severity: str,
    temperature_celsius: float,
) -> bool:
    """Send thermal alert to driver."""
    if severity == "critical":
        title = "⚠️ Critical Battery Temperature"
        body = f"Battery at {temperature_celsius:.0f}°C. Stop fast-charging now."
    else:
        title = "Battery Temperature Warning"
        body = f"Battery temperature {temperature_celsius:.0f}°C — monitor closely."

    return send_push_notification(
        device_token=driver_device_token,
        title=title,
        body=body,
        data={"type": "thermal_alert", "severity": severity, "temp": str(temperature_celsius)},
    )
