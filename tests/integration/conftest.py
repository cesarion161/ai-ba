"""Integration test fixtures with real PostgreSQL database."""

from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — ensure all models are loaded for relationship resolution

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/ai_business"


@pytest_asyncio.fixture
async def db_session():
    """Provide a clean DB session for each test with its own engine."""
    # Each test gets its own engine to avoid connection pool conflicts
    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Clean all tables (order matters for FK constraints)
        await session.execute(
            text("TRUNCATE node_artifacts, node_edges, workflow_nodes, projects, users CASCADE")
        )
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
