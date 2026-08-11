"""ChargeMesh — Auth API Routes"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DB, get_current_user
from app.config import settings
from app.models.org import OrgMember, Organization
from app.models.user import RefreshToken, User
from app.schemas.auth import (
    PasswordResetComplete,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    """Returns (raw_token, token_hash, expires_at)."""
    raw = str(uuid.uuid4())
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return raw, token_hash, expires_at


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: DB):
    # Check existing user
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="user",
    )
    db.add(user)
    await db.flush()  # get user.id

    # Issue tokens
    access = create_access_token(user.id)
    raw_refresh, token_hash, expires_at = create_refresh_token(user.id)
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))

    return TokenResponse(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: DB):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")

    access = create_access_token(user.id)
    raw_refresh, token_hash, expires_at = create_refresh_token(user.id)
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))

    return TokenResponse(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: DB):
    token_hash = hashlib.sha256(payload.refresh_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Rotate: revoke old, issue new
    token_record.revoked = True
    raw_refresh, new_hash, expires_at = create_refresh_token(token_record.user_id)
    db.add(RefreshToken(user_id=token_record.user_id, token_hash=new_hash, expires_at=expires_at))

    access = create_access_token(token_record.user_id)
    return TokenResponse(
        access_token=access,
        refresh_token=raw_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(payload: PasswordResetRequest, db: DB):
    # In production: send email with reset link and persist token with expiry.
    # WARNING: This implementation generates a token but does NOT store it in
    # the database and does NOT send an email. Password reset via this token
    # is therefore not functional. Implement token persistence and email
    # delivery before enabling this in production.
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user:
        reset_token = str(uuid.uuid4())
        logger.warning(
            "[ChargeMesh] forgot_password: reset token generated for %s but NOT "
            "stored or emailed — password reset is not fully implemented.",
            user.email,
        )
        print(f"[ChargeMesh] Password reset token for {user.email}: {reset_token}")
    return {"detail": "If that email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(payload: PasswordResetComplete, db: DB):
    # Simplified: in production would validate the reset token from email
    raise HTTPException(status_code=501, detail="Password reset via email not configured in this deployment")


@router.delete("/session", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: CurrentUser, db: DB):
    # Revoke all refresh tokens for this user
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == current_user.id, RefreshToken.revoked == False)
    )
    for token in result.scalars().all():
        token.revoked = True


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser):
    return current_user
