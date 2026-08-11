"""
ChargeMesh — Celery Worker Configuration

Queues:
  - telemetry: OEM telemetry polling and batch processing
  - dispatch: Dispatch evaluation triggered after telemetry ingestion
  - settlements: Monthly settlement report generation
  - notifications: FCM push + email notifications
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "chargemesh",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.telemetry_tasks",
        "app.tasks.dispatch_tasks",
        "app.tasks.thermal_tasks",
        "app.tasks.settlement_tasks",
        "app.tasks.station_tasks",
        "app.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # fair dispatch for long-running tasks
    task_routes={
        "app.tasks.telemetry_tasks.*": {"queue": "telemetry"},
        "app.tasks.dispatch_tasks.*": {"queue": "dispatch"},
        "app.tasks.thermal_tasks.*": {"queue": "dispatch"},
        "app.tasks.settlement_tasks.*": {"queue": "settlements"},
        "app.tasks.station_tasks.*": {"queue": "telemetry"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    beat_schedule={
        # Poll OEM telemetry every 2 minutes
        "poll-oem-telemetry": {
            "task": "app.tasks.telemetry_tasks.poll_all_oem_adapters",
            "schedule": 120.0,
            "options": {"queue": "telemetry"},
        },
        # Sync station availability every 5 minutes
        "sync-station-availability": {
            "task": "app.tasks.station_tasks.sync_all_station_availability",
            "schedule": 300.0,
            "options": {"queue": "telemetry"},
        },
        # Generate monthly settlements on the 1st of each month at 02:00 IST
        "monthly-settlements": {
            "task": "app.tasks.settlement_tasks.generate_monthly_settlements",
            "schedule": crontab(hour=2, minute=0, day_of_month=1),
            "options": {"queue": "settlements"},
        },
        # Check for sustained thermal alerts every 10 minutes
        "check-sustained-thermal-alerts": {
            "task": "app.tasks.thermal_tasks.check_sustained_alerts",
            "schedule": 600.0,
            "options": {"queue": "dispatch"},
        },
    },
)
