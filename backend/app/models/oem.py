"""ChargeMesh — OEM Adapter Models"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OEMAdapter(Base):
    __tablename__ = "oem_adapters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    oem_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_token: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted at rest
    connection_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="disconnected", server_default="disconnected"
    )
    last_telemetry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    org: Mapped["Organization"] = relationship("Organization", back_populates="oem_adapters")  # noqa: F821
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="oem_adapter")  # noqa: F821
