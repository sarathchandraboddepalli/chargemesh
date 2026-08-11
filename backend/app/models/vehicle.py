"""ChargeMesh — Vehicle and Driver Models"""

import uuid
from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    oem_adapter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("oem_adapters.id", ondelete="SET NULL"), nullable=True
    )
    registration_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    chassis_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    oem_vehicle_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    battery_capacity_kwh: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    max_range_km: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, name="current_driver_id"
    )
    current_battery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batteries.id", ondelete="SET NULL"), nullable=True, name="current_battery_id"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    org: Mapped["Organization"] = relationship("Organization", back_populates="vehicles")  # noqa: F821
    oem_adapter: Mapped["OEMAdapter | None"] = relationship("OEMAdapter", back_populates="vehicles")  # noqa: F821
    current_driver: Mapped["Driver | None"] = relationship(
        "Driver", foreign_keys=[current_driver_id], back_populates="current_vehicle"
    )
    current_battery: Mapped["Battery | None"] = relationship(  # noqa: F821
        "Battery", foreign_keys=[current_battery_id]
    )
    telemetry: Mapped[list["VehicleTelemetry"]] = relationship(  # noqa: F821
        "VehicleTelemetry", back_populates="vehicle"
    )
    charging_sessions: Mapped[list["ChargingSession"]] = relationship(  # noqa: F821
        "ChargingSession", back_populates="vehicle"
    )
    dispatch_recommendations: Mapped[list["DispatchRecommendation"]] = relationship(  # noqa: F821
        "DispatchRecommendation", back_populates="vehicle"
    )


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(15), unique=True, nullable=False)
    license_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    assigned_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True
    )
    shift_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    shift_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    org: Mapped["Organization"] = relationship("Organization", back_populates="drivers")  # noqa: F821
    user: Mapped["User | None"] = relationship("User")  # noqa: F821
    # Vehicle currently assigned to this driver (via FK on Vehicle)
    current_vehicle: Mapped["Vehicle | None"] = relationship(
        "Vehicle",
        foreign_keys="Vehicle.current_driver_id",
        back_populates="current_driver",
    )
    assigned_vehicle: Mapped["Vehicle | None"] = relationship(
        "Vehicle",
        foreign_keys=[assigned_vehicle_id],
    )
    charging_sessions: Mapped[list["ChargingSession"]] = relationship(  # noqa: F821
        "ChargingSession", back_populates="driver"
    )
