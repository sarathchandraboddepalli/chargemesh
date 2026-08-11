"""ChargeMesh — Battery and Swap Event Models"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Battery(Base):
    __tablename__ = "batteries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_battery_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    nominal_capacity_kwh: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    manufacture_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Current health metrics — updated after each swap or charge event
    current_soh: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    cycle_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_kwh_delivered: Mapped[float] = mapped_column(Numeric(10, 3), default=0, server_default="0")
    # Thermal stress index: sum(max(0, battery_temp - 35) × duration_hours) per interval
    accumulated_thermal_stress: Mapped[float] = mapped_column(Numeric(8, 2), default=0, server_default="0")

    # Status
    current_vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="available", server_default="available"
    )
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner_org: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", foreign_keys=[owner_org_id], back_populates="batteries"
    )
    current_vehicle: Mapped["Vehicle | None"] = relationship(  # noqa: F821
        "Vehicle", foreign_keys=[current_vehicle_id]
    )
    thermal_alerts: Mapped[list["ThermalAlert"]] = relationship(  # noqa: F821
        "ThermalAlert", back_populates="battery"
    )


class BatterySwap(Base):
    __tablename__ = "battery_swaps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True
    )
    removed_battery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batteries.id", ondelete="SET NULL"), nullable=True
    )
    installed_battery_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batteries.id", ondelete="SET NULL"), nullable=True
    )
    baas_vendor_org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    swap_station_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    # State of removed battery at swap time
    removed_battery_soc: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    removed_battery_soh: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    removed_battery_temp: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)

    # State of installed battery at swap time
    installed_battery_soc: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    installed_battery_soh: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Ledger data — calculated after swap
    kwh_consumed_this_session: Mapped[float | None] = mapped_column(Numeric(8, 3), nullable=True)
    degradation_this_session: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    settlement_amount_inr: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    settlement_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )

    swapped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship("Vehicle")  # noqa: F821
    driver: Mapped["Driver | None"] = relationship("Driver")  # noqa: F821
    removed_battery: Mapped["Battery | None"] = relationship("Battery", foreign_keys=[removed_battery_id])
    installed_battery: Mapped["Battery | None"] = relationship("Battery", foreign_keys=[installed_battery_id])
    baas_vendor: Mapped["Organization | None"] = relationship("Organization", foreign_keys=[baas_vendor_org_id])  # noqa: F821
