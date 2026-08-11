"""ChargeMesh — Charging Session Model"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True
    )
    station_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charging_stations.id", ondelete="SET NULL"), nullable=True
    )
    network_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charging_networks.id", ondelete="SET NULL"), nullable=True
    )
    external_session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="booked", server_default="booked"
    )
    booking_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual", server_default="manual"
    )

    # Session metrics
    soc_at_start: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    soc_at_end: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    energy_delivered_kwh: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_inr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Thermal during session
    battery_temp_at_start: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    battery_temp_max: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    battery_temp_at_end: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)

    # Timestamps
    booked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="charging_sessions")  # noqa: F821
    driver: Mapped["Driver | None"] = relationship("Driver", back_populates="charging_sessions")  # noqa: F821
    station: Mapped["ChargingStation | None"] = relationship("ChargingStation", back_populates="charging_sessions")  # noqa: F821
    network: Mapped["ChargingNetwork | None"] = relationship("ChargingNetwork")  # noqa: F821
