"""ChargeMesh — Ledger and Settlement Schemas (Pydantic v2)"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PricingConfigCreate(BaseModel):
    baas_vendor_org_id: uuid.UUID
    battery_model: str | None = None
    price_per_kwh_inr: Decimal
    price_per_soh_point_inr: Decimal = Decimal("0")
    degradation_threshold_pct: Decimal = Decimal("0.5")
    effective_from: date
    effective_to: date | None = None


class PricingConfigOut(BaseModel):
    id: uuid.UUID
    fleet_org_id: uuid.UUID
    baas_vendor_org_id: uuid.UUID
    battery_model: str | None
    price_per_kwh_inr: Decimal
    price_per_soh_point_inr: Decimal
    degradation_threshold_pct: Decimal
    effective_from: date
    effective_to: date | None
    is_active: bool

    model_config = {"from_attributes": True}


class SettlementGenerateRequest(BaseModel):
    billing_period: str  # "2026-07"
    baas_vendor_org_id: uuid.UUID | None = None  # None = generate for all vendors


class SettlementOut(BaseModel):
    id: uuid.UUID
    fleet_org_id: uuid.UUID
    baas_vendor_org_id: uuid.UUID
    billing_period: str
    total_swaps: int
    total_kwh_consumed: Decimal
    total_degradation_cost_inr: Decimal
    total_kwh_cost_inr: Decimal
    total_amount_inr: Decimal
    status: str
    approved_at: datetime | None
    approved_by: uuid.UUID | None
    generated_at: datetime

    model_config = {"from_attributes": True}


class LedgerSummary(BaseModel):
    total_pending_amount_inr: Decimal
    total_kwh_consumed: Decimal
    vendors: list[dict]
