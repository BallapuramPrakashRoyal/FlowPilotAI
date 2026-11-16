"""Database connection, engine configuration, and session management with transparent resilience."""

import logging
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

_is_fallback = False
_db_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_sqlite_path = os.path.join(_db_dir, "flowpilot.db")


def create_sqlite_engines():
    global async_engine, AsyncSessionLocal, sync_engine, SyncSessionLocal, _is_fallback
    _is_fallback = True
    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{_sqlite_path}",
        echo=False,
    )
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    sync_engine = create_engine(f"sqlite:///{_sqlite_path}")
    SyncSessionLocal = sessionmaker(bind=sync_engine)


# Primary PostgreSQL engines
_is_pg = settings.async_database_uri.startswith("postgresql")

async_engine = create_async_engine(
    settings.async_database_uri,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    **({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    } if _is_pg else {})
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

sync_engine = create_engine(
    settings.sync_database_uri,
    pool_pre_ping=True,
    **({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    } if settings.sync_database_uri.startswith("postgresql") else {})
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def check_database_health() -> dict:
    """Checks active database connectivity and returns operational metrics."""
    global _is_fallback, AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            res = await session.execute(text("SELECT 1"))
            val = res.scalar()
            return {
                "healthy": val == 1,
                "engine": "sqlite" if _is_fallback else "postgresql",
                "fallback_mode": _is_fallback,
            }
    except Exception as exc:
        return {
            "healthy": False,
            "engine": "sqlite" if _is_fallback else "postgresql",
            "fallback_mode": _is_fallback,
            "error": str(exc),
        }


def fallback_to_sqlite():
    """Switches engines to local SQLite database."""
    logger.warning("Engaging local SQLite database (flowpilot.db)...")
    create_sqlite_engines()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing database session per request with seamless fallback."""
    global _is_fallback, AsyncSessionLocal

    if _is_fallback:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return

    # Check connection on primary PostgreSQL
    connected = False
    try:
        async with AsyncSessionLocal() as session:
            await session.connection()
            connected = True
    except Exception as conn_err:
        logger.warning(f"PostgreSQL connection refused ({conn_err}). Engaging SQLite fallback.")
        fallback_to_sqlite()
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Yield session from the active provider
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
