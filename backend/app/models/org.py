"""ChargeMesh — Organization Models"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="fleet",
        server_default="fleet",
    )
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="basic",
        server_default="basic",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    members: Mapped[list["OrgMember"]] = relationship(
        "OrgMember", back_populates="org", cascade="all, delete-orphan"
    )
    vehicles: Mapped[list["Vehicle"]] = relationship("Vehicle", back_populates="org")  # noqa: F821
    drivers: Mapped[list["Driver"]] = relationship("Driver", back_populates="org")  # noqa: F821
    oem_adapters: Mapped[list["OEMAdapter"]] = relationship("OEMAdapter", back_populates="org")  # noqa: F821
    charging_networks: Mapped[list["ChargingNetwork"]] = relationship("ChargingNetwork", back_populates="org")  # noqa: F821
    batteries: Mapped[list["Battery"]] = relationship("Battery", foreign_keys="Battery.owner_org_id", back_populates="owner_org")  # noqa: F821


class OrgMember(Base):
    __tablename__ = "org_members"
    __table_args__ = (UniqueConstraint("org_id", "user_id", name="uq_org_member"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member", server_default="member")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    org: Mapped["Organization"] = relationship("Organization", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="org_memberships")  # noqa: F821
