import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.models import Base

# Separate test database on the same Postgres server.
TEST_DB_URL = settings.DATABASE_URL.rsplit("/", 1)[0] + "/socialhub_test"

_TABLES = "users, posts, comments, reactions, shares, refresh_tokens"


async def _ensure_test_database() -> None:
    """Create socialhub_test if it doesn't exist (connects to the default DB)."""
    admin = create_async_engine(
        settings.DATABASE_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'socialhub_test'")
        )
        if not exists:
            await conn.execute(text("CREATE DATABASE socialhub_test"))
    await admin.dispose()


@pytest_asyncio.fixture
async def engine():
    await _ensure_test_database()
    eng = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    # Clean all rows so each test starts fresh.
    async with eng.begin() as conn:
        await conn.execute(text(f"TRUNCATE {_TABLES} RESTART IDENTITY CASCADE"))
    await eng.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncSession:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(engine) -> AsyncClient:
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(client) -> dict:
    """A registered user; returns the register response (tokens + user)."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
            "display_name": "Alice",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest_asyncio.fixture
async def auth_client(client, user) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {user['access_token']}"
    return client


@pytest_asyncio.fixture
async def second_user(client) -> dict:
    """A second registered user (for ownership / multi-user tests)."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "carol",
            "email": "carol@example.com",
            "password": "password123",
            "display_name": "Carol",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth_header(token_holder: dict) -> dict:
    """Build an Authorization header from a register/login response."""
    return {"Authorization": f"Bearer {token_holder['access_token']}"}


@pytest_asyncio.fixture
async def post(client, user) -> dict:
    """A post authored by `user` (alice). Uses explicit auth, not the shared header."""
    resp = await client.post(
        "/api/v1/posts", json={"content": "Hello world"}, headers=auth_header(user)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
