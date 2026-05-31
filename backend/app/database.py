"""Async SQLAlchemy engine + session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# Required for Supabase Supavisor / PgBouncer in Transaction mode, which
# does not support prepared statements. It is an asyncpg-only connect arg,
# so we only pass it for PostgreSQL — SQLite (aiosqlite, used by tests and
# the `make run` quickstart) rejects unknown kwargs with a TypeError.
_connect_args: dict[str, object] = {}
if "asyncpg" in settings.database_url:
    _connect_args["statement_cache_size"] = 0

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a database session."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create tables if they do not exist (idempotent)."""
    from app import models  # noqa: F401 - ensure models are registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
