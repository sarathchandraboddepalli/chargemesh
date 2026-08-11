"""
ChargeMesh — Test Configuration and Fixtures
Uses SQLite in-memory with PostgreSQL dialect patches for portability.
"""

# ── SQLite compatibility patches (MUST precede all app imports) ───────────────
import json as _json
import sqlalchemy.dialects.postgresql as _pg
from sqlalchemy import types as _t


class _UUID(_t.TypeDecorator):
    """Store UUID as varchar(36) in SQLite."""
    impl = _t.String(36)
    cache_ok = True

    def __init__(self, as_uuid: bool = False, **kw):  # noqa: ARG002
        super().__init__(**kw)

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        import uuid as _uuid_mod
        if value is None:
            return None
        try:
            return _uuid_mod.UUID(str(value))
        except (ValueError, AttributeError):
            return value


class _JSONB(_t.TypeDecorator):
    """Store JSONB as JSON text in SQLite."""
    impl = _t.Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return _json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return _json.loads(value) if value is not None else None


class _ARRAY(_t.TypeDecorator):
    """Store ARRAY as JSON text in SQLite."""
    impl = _t.Text
    cache_ok = True

    def __init__(self, item_type=None, **kw):  # noqa: ARG002
        super().__init__(**kw)

    def process_bind_param(self, value, dialect):
        return _json.dumps(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return _json.loads(value) if value is not None else []


_pg.UUID = _UUID
_pg.JSONB = _JSONB
_pg.ARRAY = _ARRAY
_pg.INET = _t.String(45)

import sqlalchemy as _sa  # noqa: E402
_sa.ARRAY = _ARRAY
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-for-testing-only-32chars")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
os.environ.setdefault("OEM_MODE", "mock")
os.environ.setdefault("CHARGING_NETWORK_MODE", "mock")
os.environ.setdefault("EMAIL_BACKEND", "console")
os.environ.setdefault("MAPBOX_ACCESS_TOKEN", "test-token")
os.environ.setdefault("THERMAL_WARNING_THRESHOLD", "42")
os.environ.setdefault("THERMAL_CRITICAL_THRESHOLD", "48")
os.environ.setdefault("DISPATCH_SOC_THRESHOLD", "25")
os.environ.setdefault("DISPATCH_SAFETY_BUFFER_KM", "10")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.org import OrgMember, Organization  # noqa: E402
from app.models.user import User  # noqa: E402

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    from app.api.v1.auth import hash_password
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@chargemesh.in",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        role="user",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_org(db_session, test_user) -> Organization:
    org = Organization(name="Test Fleet", org_type="fleet", tier="premium")
    db_session.add(org)
    await db_session.flush()
    db_session.add(OrgMember(org_id=org.id, user_id=test_user.id, role="owner"))
    await db_session.flush()
    return org


@pytest.fixture
def auth_headers(test_user) -> dict:
    from app.api.v1.auth import create_access_token
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
