"""ChargeMesh — Dispatch Recommendation Model"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DispatchRecommendation(Base):
    """
    Records when ChargeMesh determines a vehicle needs charging and
    recommends a specific charging station.

    Tracks whether recommendations were acted upon for dispatch accuracy analytics.
    """
    __tablename__ = "dispatch_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommended_station_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charging_stations.id", ondelete="SET NULL"), nullable=True
    )
    trigger_soc: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    predicted_depletion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recommended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    was_acted_upon: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("charging_sessions.id", ondelete="SET NULL"), nullable=True
    )
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    org: Mapped["Organization"] = relationship("Organization")  # noqa: F821
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="dispatch_recommendations")  # noqa: F821
    recommended_station: Mapped["ChargingStation | None"] = relationship(  # noqa: F821
        "ChargingStation", back_populates="dispatch_recommendations"
    )
    session: Mapped["ChargingSession | None"] = relationship("ChargingSession")  # noqa: F821
    overrider: Mapped["User | None"] = relationship("User")  # noqa: F821
