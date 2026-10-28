"""Pytest configuration and shared fixtures."""
import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base
from app.db.session import get_db
from app.main import app

# Use an in-memory SQLite DB for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Override env vars before app imports pick them up
os.environ.setdefault("MPESA_CONSUMER_KEY", "test_consumer_key")
os.environ.setdefault("MPESA_CONSUMER_SECRET", "test_consumer_secret")
os.environ.setdefault("MPESA_LIPA_NA_MPESA_PASSKEY", "test_passkey")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create an isolated in-memory database per test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession):
    """HTTP test client with overridden DB dependency."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
