"""
ChargeMesh — FastAPI Dependencies
Provides: get_db, get_current_user, get_current_org, require_role
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.org import OrgMember, Organization
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT and return the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id), User.is_active == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_org(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Return the organization of the authenticated user (first membership)."""
    result = await db.execute(
        select(Organization)
        .join(OrgMember, OrgMember.org_id == Organization.id)
        .where(OrgMember.user_id == current_user.id, Organization.is_active == True)
        .limit(1)
    )
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to any organization",
        )
    return org


async def get_current_membership(
    current_user: Annotated[User, Depends(get_current_user)],
    current_org: Annotated[Organization, Depends(get_current_org)],
    db: AsyncSession = Depends(get_db),
) -> OrgMember:
    result = await db.execute(
        select(OrgMember).where(
            OrgMember.user_id == current_user.id,
            OrgMember.org_id == current_org.id,
        )
    )
    return result.scalar_one()


def require_role(*roles: str):
    """Dependency factory: enforces that current user has one of the given roles."""
    async def _check(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(roles)}",
            )
        return user
    return _check


def require_org_role(*roles: str):
    """Dependency factory: enforces that user's membership role is in roles."""
    async def _check(
        membership: Annotated[OrgMember, Depends(get_current_membership)],
    ) -> OrgMember:
        if membership.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires org role: {', '.join(roles)}",
            )
        return membership
    return _check


# Type aliases for common patterns
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentOrg = Annotated[Organization, Depends(get_current_org)]
DB = Annotated[AsyncSession, Depends(get_db)]
