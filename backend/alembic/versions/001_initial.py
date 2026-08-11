"""Initial schema — all tables + TimescaleDB hypertable for vehicle_telemetry

Revision ID: 001_initial
Revises:
Create Date: 2026-08-07

IMPORTANT: This migration calls SELECT create_hypertable('vehicle_telemetry', 'recorded_at')
which converts vehicle_telemetry into a TimescaleDB hypertable partitioned by time.
This MUST run on a TimescaleDB-enabled PostgreSQL instance.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable required PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
    op.execute("CREATE EXTENSION IF NOT EXISTS cube")
    op.execute("CREATE EXTENSION IF NOT EXISTS earthdistance")

    # ── Users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(15), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("role IN ('user', 'driver', 'admin')", name="ck_user_role"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── Refresh Tokens ─────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ── Organizations ──────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("org_type", sa.String(20), nullable=False, server_default="fleet"),
        sa.Column("tier", sa.String(20), nullable=False, server_default="basic"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "org_type IN ('fleet', 'baas_vendor', 'charging_network', 'platform_admin')",
            name="ck_org_type",
        ),
        sa.CheckConstraint("tier IN ('basic', 'premium', 'enterprise')", name="ck_org_tier"),
    )

    # ── Org Members ────────────────────────────────────────────────────────────
    op.create_table(
        "org_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_member"),
        sa.CheckConstraint("role IN ('owner', 'admin', 'member', 'viewer')", name="ck_member_role"),
    )

    # ── OEM Adapters ───────────────────────────────────────────────────────────
    op.create_table(
        "oem_adapters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("oem_slug", sa.String(50), nullable=False),
        sa.Column("api_key_hash", sa.String(255), nullable=True),
        sa.Column("base_url", sa.String(255), nullable=True),
        sa.Column("auth_token", sa.Text(), nullable=True),
        sa.Column("connection_status", sa.String(20), nullable=False, server_default="disconnected"),
        sa.Column("last_telemetry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "connection_status IN ('connected', 'disconnected', 'error')",
            name="ck_oem_connection_status",
        ),
    )

    # ── Charging Networks ──────────────────────────────────────────────────────
    op.create_table(
        "charging_networks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("network_slug", sa.String(50), nullable=False),
        sa.Column("integration_type", sa.String(20), nullable=False),
        sa.Column("api_base_url", sa.String(255), nullable=True),
        sa.Column("auth_token", sa.Text(), nullable=True),
        sa.Column("ocpp_server_url", sa.String(255), nullable=True),
        sa.Column("connection_status", sa.String(20), nullable=False, server_default="disconnected"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("station_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "integration_type IN ('ocpp_1_6', 'ocpp_2_0', 'proprietary')",
            name="ck_network_integration_type",
        ),
    )

    # ── Charging Stations ──────────────────────────────────────────────────────
    op.create_table(
        "charging_stations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charging_networks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_station_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("total_connectors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_connectors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("connector_types", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("max_power_kw", sa.Numeric(6, 1), nullable=True),
        sa.Column("pricing_per_kwh", sa.Numeric(8, 2), nullable=True),
        sa.Column("is_operational", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_status_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("network_id", "external_station_id", name="uq_station_network_external"),
    )
    op.create_index("ix_stations_network", "charging_stations", ["network_id", "is_operational"])

    # ── Vehicles (no driver/battery FKs yet — added after those tables exist) ──
    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("oem_adapter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("oem_adapters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("registration_number", sa.String(20), nullable=False, unique=True),
        sa.Column("chassis_number", sa.String(50), nullable=True),
        sa.Column("oem_vehicle_id", sa.String(100), nullable=True),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("battery_capacity_kwh", sa.Numeric(6, 2), nullable=True),
        sa.Column("max_range_km", sa.Numeric(6, 1), nullable=True),
        sa.Column("zone", sa.String(100), nullable=True),
        sa.Column("current_driver_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added below
        sa.Column("current_battery_id", postgresql.UUID(as_uuid=True), nullable=True),  # FK added below
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('active', 'charging', 'swapping', 'maintenance', 'inactive')",
            name="ck_vehicle_status",
        ),
    )
    op.create_index("ix_vehicles_org", "vehicles", ["org_id"])
    op.create_index("ix_vehicles_status", "vehicles", ["org_id", "status"])

    # ── Drivers ────────────────────────────────────────────────────────────────
    op.create_table(
        "drivers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(15), nullable=False, unique=True),
        sa.Column("license_number", sa.String(50), nullable=True),
        sa.Column("assigned_vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("shift_start", sa.Time(), nullable=True),
        sa.Column("shift_end", sa.Time(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_drivers_org", "drivers", ["org_id"])

    # Add deferred FKs on vehicles now that drivers table exists
    op.create_foreign_key(
        "fk_vehicle_driver", "vehicles", "drivers", ["current_driver_id"], ["id"], ondelete="SET NULL"
    )

    # ── Batteries ──────────────────────────────────────────────────────────────
    op.create_table(
        "batteries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("owner_org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_battery_id", sa.String(100), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("nominal_capacity_kwh", sa.Numeric(6, 2), nullable=True),
        sa.Column("manufacture_date", sa.Date(), nullable=True),
        sa.Column("current_soh", sa.Numeric(5, 2), nullable=True),
        sa.Column("cycle_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_kwh_delivered", sa.Numeric(10, 3), nullable=False, server_default="0"),
        sa.Column("accumulated_thermal_stress", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("current_vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("flag_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('installed', 'available', 'charging', 'retired', 'maintenance')",
            name="ck_battery_status",
        ),
    )
    op.create_index("ix_batteries_owner", "batteries", ["owner_org_id"])
    op.create_index("ix_batteries_vehicle", "batteries", ["current_vehicle_id"])

    # Add deferred FK on vehicles now that batteries table exists
    op.create_foreign_key(
        "fk_vehicle_battery", "vehicles", "batteries", ["current_battery_id"], ["id"], ondelete="SET NULL"
    )

    # ── Vehicle Telemetry (TimescaleDB Hypertable) ─────────────────────────────
    op.create_table(
        "vehicle_telemetry",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, primary_key=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, primary_key=True),
        sa.Column("state_of_charge", sa.Numeric(5, 2), nullable=True),
        sa.Column("state_of_health", sa.Numeric(5, 2), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("speed_kmh", sa.Numeric(6, 1), nullable=True),
        sa.Column("battery_temp_celsius", sa.Numeric(5, 1), nullable=True),
        sa.Column("ambient_temp_celsius", sa.Numeric(5, 1), nullable=True),
        sa.Column("odometer_km", sa.Numeric(10, 1), nullable=True),
        sa.Column("is_charging", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("charging_power_kw", sa.Numeric(6, 2), nullable=True),
        sa.Column("estimated_range_km", sa.Numeric(6, 1), nullable=True),
        sa.Column("battery_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_telemetry_vehicle", "vehicle_telemetry", ["vehicle_id", sa.text("recorded_at DESC")])

    # CRITICAL: Convert vehicle_telemetry to TimescaleDB hypertable
    # This partitions the table by recorded_at for efficient time-range queries.
    # Without this, querying 7.2M rows/day becomes unacceptably slow within weeks.
    op.execute(
        "SELECT create_hypertable('vehicle_telemetry', 'recorded_at', "
        "chunk_time_interval => INTERVAL '1 day', "
        "if_not_exists => TRUE)"
    )

    # ── Charging Sessions ──────────────────────────────────────────────────────
    op.create_table(
        "charging_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charging_stations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charging_networks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_session_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="booked"),
        sa.Column("booking_type", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("soc_at_start", sa.Numeric(5, 2), nullable=True),
        sa.Column("soc_at_end", sa.Numeric(5, 2), nullable=True),
        sa.Column("energy_delivered_kwh", sa.Numeric(8, 3), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("cost_inr", sa.Numeric(10, 2), nullable=True),
        sa.Column("battery_temp_at_start", sa.Numeric(5, 1), nullable=True),
        sa.Column("battery_temp_max", sa.Numeric(5, 1), nullable=True),
        sa.Column("battery_temp_at_end", sa.Numeric(5, 1), nullable=True),
        sa.Column("booked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('booked', 'active', 'completed', 'cancelled', 'failed')",
            name="ck_session_status",
        ),
        sa.CheckConstraint(
            "booking_type IN ('manual', 'dispatch', 'driver')",
            name="ck_session_booking_type",
        ),
    )
    op.create_index("ix_sessions_vehicle", "charging_sessions", ["vehicle_id", sa.text("started_at DESC")])
    op.create_index("ix_sessions_status", "charging_sessions", ["status"])

    # ── Battery Swaps ──────────────────────────────────────────────────────────
    op.create_table(
        "battery_swaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("removed_battery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("batteries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("installed_battery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("batteries.id", ondelete="SET NULL"), nullable=True),
        sa.Column("baas_vendor_org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("swap_station_name", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("removed_battery_soc", sa.Numeric(5, 2), nullable=True),
        sa.Column("removed_battery_soh", sa.Numeric(5, 2), nullable=True),
        sa.Column("removed_battery_temp", sa.Numeric(5, 1), nullable=True),
        sa.Column("installed_battery_soc", sa.Numeric(5, 2), nullable=True),
        sa.Column("installed_battery_soh", sa.Numeric(5, 2), nullable=True),
        sa.Column("kwh_consumed_this_session", sa.Numeric(8, 3), nullable=True),
        sa.Column("degradation_this_session", sa.Numeric(6, 4), nullable=True),
        sa.Column("settlement_amount_inr", sa.Numeric(10, 2), nullable=True),
        sa.Column("settlement_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("swapped_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "settlement_status IN ('pending', 'included_in_report', 'settled')",
            name="ck_swap_settlement_status",
        ),
    )
    op.create_index("ix_swaps_vehicle", "battery_swaps", ["vehicle_id", sa.text("swapped_at DESC")])
    op.create_index("ix_swaps_settlement", "battery_swaps", ["settlement_status"])

    # ── BaaS Pricing Config ────────────────────────────────────────────────────
    op.create_table(
        "baas_pricing_config",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("fleet_org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("baas_vendor_org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("battery_model", sa.String(100), nullable=True),
        sa.Column("price_per_kwh_inr", sa.Numeric(8, 4), nullable=False),
        sa.Column("price_per_soh_point_inr", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("degradation_threshold_pct", sa.Numeric(4, 2), nullable=False, server_default="0.5"),
        sa.Column("currency", sa.String(5), nullable=False, server_default="INR"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint(
            "fleet_org_id", "baas_vendor_org_id", "battery_model", "effective_from",
            name="uq_pricing_config",
        ),
    )

    # ── Settlement Reports ─────────────────────────────────────────────────────
    op.create_table(
        "settlement_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("fleet_org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("baas_vendor_org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("billing_period", sa.String(7), nullable=False),
        sa.Column("total_swaps", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_kwh_consumed", sa.Numeric(12, 3), nullable=False, server_default="0"),
        sa.Column("total_degradation_cost_inr", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_kwh_cost_inr", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("total_amount_inr", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('draft', 'approved', 'paid')", name="ck_settlement_status"),
    )

    # ── Thermal Alerts ─────────────────────────────────────────────────────────
    op.create_table(
        "thermal_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("battery_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("batteries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False, server_default="warning"),
        sa.Column("temperature_celsius", sa.Numeric(5, 1), nullable=True),
        sa.Column("threshold_celsius", sa.Numeric(5, 1), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "alert_type IN ('high_temp', 'sustained_high_temp', 'rapid_temp_rise', 'above_threshold_degradation', 'projected_early_retirement')",
            name="ck_alert_type",
        ),
        sa.CheckConstraint("severity IN ('info', 'warning', 'critical')", name="ck_alert_severity"),
    )
    op.create_index("ix_thermal_alerts_active", "thermal_alerts", ["org_id", "is_resolved", sa.text("created_at DESC")])

    # ── Dispatch Recommendations ───────────────────────────────────────────────
    op.create_table(
        "dispatch_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommended_station_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charging_stations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("trigger_soc", sa.Numeric(5, 2), nullable=True),
        sa.Column("predicted_depletion_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recommended_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("was_acted_upon", sa.Boolean(), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("charging_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("overridden_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_dispatch_recs_vehicle", "dispatch_recommendations", ["vehicle_id", sa.text("recommended_at DESC")])


def downgrade() -> None:
    op.drop_table("dispatch_recommendations")
    op.drop_table("thermal_alerts")
    op.drop_table("settlement_reports")
    op.drop_table("baas_pricing_config")
    op.drop_table("battery_swaps")
    op.drop_table("charging_sessions")
    op.drop_table("vehicle_telemetry")
    op.drop_constraint("fk_vehicle_battery", "vehicles", type_="foreignkey")
    op.drop_table("batteries")
    op.drop_constraint("fk_vehicle_driver", "vehicles", type_="foreignkey")
    op.drop_table("drivers")
    op.drop_table("vehicles")
    op.drop_table("charging_stations")
    op.drop_table("charging_networks")
    op.drop_table("oem_adapters")
    op.drop_table("org_members")
    op.drop_table("organizations")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
