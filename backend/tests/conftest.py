"""Pytest fixtures and isolated test database management for FlowPilot AI."""

import os
import sys
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import Base, get_db
import app.core.database as db_mod
import app.database.models  # Ensure all SQLAlchemy models are registered in Base.metadata
from app.main import app

# Determine isolated test database path
_ci_db = os.environ.get("DATABASE_URL")
if _ci_db and ("test" in _ci_db.lower() or "ci" in _ci_db.lower()):
    TEST_ASYNC_DB_URL = _ci_db
else:
    _test_db_path = os.path.join(backend_dir, "tests", "flowpilot_test_isolated.db")
    TEST_ASYNC_DB_URL = f"sqlite+aiosqlite:///{_test_db_path}"

_test_sync_url = TEST_ASYNC_DB_URL.replace("sqlite+aiosqlite:///", "sqlite:///")

# Create shared test engines
test_sync_engine = create_engine(_test_sync_url)
test_async_engine = create_async_engine(TEST_ASYNC_DB_URL, echo=False)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
TestSyncSessionLocal = sessionmaker(bind=test_sync_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database_schema():
    """Session-level sync schema creation: ensures all models exist before any test runs."""
    # Ensure all tables exist in the isolated test database
    Base.metadata.create_all(test_sync_engine)
    yield
    # Cleanup on session end
    db_file = TEST_ASYNC_DB_URL.replace("sqlite+aiosqlite:///", "")
    if os.path.exists(db_file) and "flowpilot_test_isolated.db" in db_file:
        try:
            os.remove(db_file)
        except Exception:
            pass


@pytest.fixture(autouse=True)
async def setup_test_db_context():
    """Function-level fixture: binds FastAPI get_db and db_mod to the test engines."""
    orig_async_engine = db_mod.async_engine
    orig_async_session = db_mod.AsyncSessionLocal
    orig_sync_engine = db_mod.sync_engine
    orig_sync_session = db_mod.SyncSessionLocal
    orig_fallback = db_mod._is_fallback

    db_mod.async_engine = test_async_engine
    db_mod.AsyncSessionLocal = TestAsyncSessionLocal
    db_mod.sync_engine = test_sync_engine
    db_mod.SyncSessionLocal = TestSyncSessionLocal
    db_mod._is_fallback = True

    async def override_get_db():
        async with TestAsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    db_mod.async_engine = orig_async_engine
    db_mod.AsyncSessionLocal = orig_async_session
    db_mod.sync_engine = orig_sync_engine
    db_mod.SyncSessionLocal = orig_sync_session
    db_mod._is_fallback = orig_fallback
