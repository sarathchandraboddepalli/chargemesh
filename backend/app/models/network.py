"""ChargeMesh — Charging Network and Station Models"""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChargingNetwork(Base):
    __tablename__ = "charging_networks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    network_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    integration_type: Mapped[str] = mapped_column(String(20), nullable=False)
    api_base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_token: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted
    ocpp_server_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    connection_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="disconnected", server_default="disconnected"
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    station_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    org: Mapped["Organization"] = relationship("Organization", back_populates="charging_networks")  # noqa: F821
    stations: Mapped[list["ChargingStation"]] = relationship(
        "ChargingStation", back_populates="network", cascade="all, delete-orphan"
    )


class ChargingStation(Base):
    __tablename__ = "charging_stations"
    __table_args__ = (
        UniqueConstraint("network_id", "external_station_id", name="uq_station_network_external"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charging_networks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_station_id: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    total_connectors: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    available_connectors: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    connector_types: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)), nullable=True)
    max_power_kw: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    pricing_per_kwh: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    is_operational: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    last_status_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    network: Mapped["ChargingNetwork"] = relationship("ChargingNetwork", back_populates="stations")
    charging_sessions: Mapped[list["ChargingSession"]] = relationship(  # noqa: F821
        "ChargingSession", back_populates="station"
    )
    dispatch_recommendations: Mapped[list["DispatchRecommendation"]] = relationship(  # noqa: F821
        "DispatchRecommendation", back_populates="recommended_station"
    )
