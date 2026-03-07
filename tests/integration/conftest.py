"""Integration test fixtures with real PostgreSQL database.

Uses a dedicated 'ai_business_test' database so tests never touch dev data.
The database is auto-created if it doesn't exist.
"""

from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — ensure all models are loaded for relationship resolution
from app.models.database import Base  # used for sorted_tables in TRUNCATE

# Separate test database — never wipes the dev database
_PG_ADMIN_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/postgres"
_TEST_DB_NAME = "ai_business_test"
TEST_DB_URL = f"postgresql+asyncpg://postgres:postgres@localhost:5433/{_TEST_DB_NAME}"


async def _ensure_test_db() -> None:
    """Create the test database if it doesn't exist."""
    engine = create_async_engine(_PG_ADMIN_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": _TEST_DB_NAME},
        )
        if not result.scalar():
            await conn.execute(text(f"CREATE DATABASE {_TEST_DB_NAME}"))
    await engine.dispose()


def _run_migrations():
    """Run Alembic migrations against the test database."""
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config("alembic.ini")
    sync_url = TEST_DB_URL.replace("+asyncpg", "")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture
async def db_session():
    """Provide a clean DB session for each test with its own engine."""
    await _ensure_test_db()
    _run_migrations()

    test_engine = create_async_engine(TEST_DB_URL, echo=False)

    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Clean all tables — use metadata to get the actual table list
        table_names = [t.name for t in reversed(Base.metadata.sorted_tables)]
        if table_names:
            await session.execute(text(f"TRUNCATE {', '.join(table_names)} CASCADE"))
        await session.commit()
        yield session

    await test_engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user and return their ID."""
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Create an async test client with DB session override."""
    from app.core.security import hash_password
    from app.models.user import User

    # Create the placeholder user that project routes expect
    placeholder_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        email="placeholder@test.com",
        hashed_password=hash_password("placeholder"),
    )
    db_session.add(placeholder_user)
    await db_session.commit()

    from app.main import create_app
    from app.models.database import get_db

    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
