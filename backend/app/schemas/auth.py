"""ChargeMesh — Auth Schemas (Pydantic v2)"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    email: EmailStr
    phone: str | None = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    password: str = Field(min_length=8)
    full_name: str | None = None

    model_config = {"str_strip_whitespace": True}


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = {"str_strip_whitespace": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetComplete(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    phone: str | None
    full_name: str | None
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}
