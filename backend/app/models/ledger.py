"""ChargeMesh — BaaS Ledger and Settlement Models"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BaaSPricingConfig(Base):
    """Pricing contract between a fleet operator and a BaaS vendor."""
    __tablename__ = "baas_pricing_config"
    __table_args__ = (
        UniqueConstraint(
            "fleet_org_id", "baas_vendor_org_id", "battery_model", "effective_from",
            name="uq_pricing_config"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fleet_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    baas_vendor_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    battery_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_per_kwh_inr: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    # Additional charge per % SoH degraded above the normal degradation threshold
    price_per_soh_point_inr: Mapped[float] = mapped_column(Numeric(10, 4), default=0, server_default="0")
    # Normal degradation per 100 kWh — anything above this triggers the SoH surcharge
    degradation_threshold_pct: Mapped[float] = mapped_column(Numeric(4, 2), default=0.5, server_default="0.5")
    currency: Mapped[str] = mapped_column(String(5), default="INR", server_default="INR")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    fleet_org: Mapped["Organization"] = relationship("Organization", foreign_keys=[fleet_org_id])  # noqa: F821
    baas_vendor_org: Mapped["Organization"] = relationship("Organization", foreign_keys=[baas_vendor_org_id])  # noqa: F821


class SettlementReport(Base):
    """Monthly settlement report between a fleet org and a BaaS vendor."""
    __tablename__ = "settlement_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fleet_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    baas_vendor_org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    billing_period: Mapped[str] = mapped_column(String(7), nullable=False)  # "2026-07"
    total_swaps: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_kwh_consumed: Mapped[float] = mapped_column(Numeric(12, 3), default=0, server_default="0")
    total_degradation_cost_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    total_kwh_cost_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    total_amount_inr: Mapped[float] = mapped_column(Numeric(12, 2), default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    fleet_org: Mapped["Organization"] = relationship("Organization", foreign_keys=[fleet_org_id])  # noqa: F821
    baas_vendor_org: Mapped["Organization"] = relationship("Organization", foreign_keys=[baas_vendor_org_id])  # noqa: F821
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])  # noqa: F821
