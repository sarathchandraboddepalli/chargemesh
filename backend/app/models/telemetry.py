"""
ChargeMesh — Vehicle Telemetry Model (TimescaleDB Hypertable)

The vehicle_telemetry table is the core time-series store. It uses a
composite primary key (vehicle_id, recorded_at) to ensure idempotent
inserts — OEM adapters may retry on network failure.

TimescaleDB converts this table into a hypertable partitioned by
recorded_at. At 1-minute intervals for 5,000 vehicles, this generates
~7.2M rows/day. TimescaleDB chunks provide efficient range queries
without full table scans.

Migration note: After creating this table, run:
    SELECT create_hypertable('vehicle_telemetry', 'recorded_at');
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VehicleTelemetry(Base):
    __tablename__ = "vehicle_telemetry"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        primary_key=True,
    )

    # State of Charge and Health
    state_of_charge: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    state_of_health: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Location (from OEM telematics — NOT from driver's phone)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    # Motion
    speed_kmh: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    odometer_km: Mapped[float | None] = mapped_column(Numeric(10, 1), nullable=True)

    # Thermal data — critical for BaaS settlement and thermal stress index
    battery_temp_celsius: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    ambient_temp_celsius: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)

    # Charging state
    is_charging: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    charging_power_kw: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    # Derived
    estimated_range_km: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)

    # Battery tracking (for BaaS multi-vendor support)
    battery_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Full OEM payload for debugging and reprocessing
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="telemetry")  # noqa: F821
