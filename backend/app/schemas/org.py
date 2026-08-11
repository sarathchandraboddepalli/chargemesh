"""ChargeMesh — Organization Schemas (Pydantic v2)"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class OrgCreate(BaseModel):
    name: str
    org_type: str = "fleet"  # fleet, baas_vendor, charging_network, platform_admin

    model_config = {"str_strip_whitespace": True}


class OrgUpdate(BaseModel):
    name: str | None = None
    tier: str | None = None


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    org_type: str
    tier: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberInvite(BaseModel):
    email: EmailStr
    role: str = "member"


class MemberOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    user_email: str | None = None
    user_name: str | None = None

    model_config = {"from_attributes": True}
