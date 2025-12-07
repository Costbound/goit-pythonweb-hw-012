import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from redis.asyncio import Redis
from typing import AsyncGenerator

from main import app
from src.database.models import Base, User
from src.database.db import get_db
from src.database.redis import get_redis
from src.services.auth import create_access_token, Hash


SQLALCHEMY_DATABASE_URL = (
    os.getenv("TEST_DATABASE_URL")
    or "postgresql+asyncpg://postgres:test_password@localhost:5433/goit-pythonweb-hw-12-test"
)
REDIS_URL = os.getenv("TEST_REDIS_URL") or "redis://localhost:6380/0"

test_user = {
    "email": "deadpool@example.com",
    "password": "12345678",
}


@pytest_asyncio.fixture(scope="function")
async def async_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Session-scoped async engine, created once per test session.
    Bound to pytest-asyncio's event loop.
    """
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="function")
def testing_session_local(async_engine: AsyncEngine):
    """
    Session factory bound to the session-scoped engine.
    """
    return async_sessionmaker(
        bind=async_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_db(async_engine: AsyncEngine):
    """
    Drop and recreate all tables before each test.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(testing_session_local):
    """
    Provide a clean DB session for each test.
    """
    async with testing_session_local() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def redis_session():
    """
    Real Redis client for tests on localhost:6380.
    Flush DB before and after each test.
    """
    client = Redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest_asyncio.fixture(scope="function")
async def client(testing_session_local, redis_session):
    """
    Async HTTP client with overridden DB and Redis dependencies.
    """

    async def override_get_db():
        async with testing_session_local() as session:
            try:
                yield session
            finally:
                await session.close()

    async def override_get_redis():
        yield redis_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user_in_db(db_session):
    """
    Create a verified test user in DB.
    """
    hash_password = Hash().get_password_hash(test_user["password"])
    current_user = User(
        email=test_user["email"],
        password_hash=hash_password,
        email_verified=True,
        avatar_url="https://www.gravatar.com/avatar/test",
    )
    db_session.add(current_user)
    await db_session.commit()
    await db_session.refresh(current_user)
    return current_user


@pytest_asyncio.fixture(scope="function")
async def get_token(test_user_in_db):
    """
    Generate an access token for the test user.
    """
    token = await create_access_token(data={"sub": test_user_in_db.email})
    return token


@pytest_asyncio.fixture
async def authorized_client(client: AsyncClient, get_token: str) -> AsyncClient:
    """Client with authorization header."""
    client.headers.update({"Authorization": f"Bearer {get_token}"})
    return client


@pytest_asyncio.fixture
async def create_authenticated_user(client: AsyncClient, db_session):
    """Factory fixture to create and authenticate users."""

    async def _create_user(email: str, password: str):
        """Create a new user and return their token."""
        # Create user directly in database
        password_hash = Hash().get_password_hash(password)
        user = User(
            email=email,
            password_hash=password_hash,
            email_verified=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create access token
        token = await create_access_token(data={"sub": user.email})
        return token, user

    return _create_user
