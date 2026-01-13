import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.main import app
from app.models import Base, User, Post, Comment, Like, EmailVerificationToken
from app.dependencies import get_db
from app.core.security import get_password_hash, generate_verification_token


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

_test_session = None


async def override_get_db():
    global _test_session
    if _test_session:
        yield _test_session
    else:
        async with TestingSessionLocal() as session:
            yield session


app.dependency_overrides[get_db] = override_get_db

from app.core.limiter import limiter
limiter.enabled = False


@pytest_asyncio.fixture
async def db_session():
    global _test_session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        _test_session = session
        yield session
        _test_session = None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client(db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "password123"
    }


@pytest.fixture
def test_user_data_2():
    return {
        "email": "test2@example.com",
        "username": "testuser2",
        "full_name": "Test User 2",
        "password": "password456"
    }


@pytest.fixture
def test_post_data():
    return {
        "title": "Test Post Title",
        "content": "This is the content of the test post with enough characters."
    }


@pytest.fixture
def test_comment_data():
    return {
        "content": "This is a test comment."
    }


async def register_user(client: AsyncClient, user_data: dict) -> dict:
    with patch("app.services.auth_service.send_email_task"):
        response = await client.post("/auth/register", json=user_data)
    return response.json()


async def login_user(client: AsyncClient, email: str, password: str) -> str:
    response = await client.post(
        "/auth/login",
        data={"username": email, "password": password}
    )
    return response.json()["access_token"]


async def get_auth_header(client: AsyncClient, user_data: dict) -> dict:
    await register_user(client, user_data)
    token = await login_user(client, user_data["email"], user_data["password"])
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def verified_user(async_client, test_user_data, db_session):
    user_response = await register_user(async_client, test_user_data)
    
    from sqlalchemy import update
    await db_session.execute(
        update(User).where(User.email == test_user_data["email"]).values(is_verified=True)
    )
    await db_session.commit()
    
    token = await login_user(async_client, test_user_data["email"], test_user_data["password"])
    
    return {
        "user": user_response,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "data": test_user_data
    }


@pytest_asyncio.fixture
async def unverified_user(async_client, test_user_data):
    user_response = await register_user(async_client, test_user_data)
    token = await login_user(async_client, test_user_data["email"], test_user_data["password"])
    
    return {
        "user": user_response,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "data": test_user_data
    }


@pytest_asyncio.fixture
async def second_verified_user(async_client, test_user_data_2, db_session):
    user_response = await register_user(async_client, test_user_data_2)
    
    from sqlalchemy import update
    await db_session.execute(
        update(User).where(User.email == test_user_data_2["email"]).values(is_verified=True)
    )
    await db_session.commit()
    
    token = await login_user(async_client, test_user_data_2["email"], test_user_data_2["password"])
    
    return {
        "user": user_response,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
        "data": test_user_data_2
    }


@pytest_asyncio.fixture
async def user_with_post(async_client, verified_user, test_post_data):
    response = await async_client.post(
        "/posts",
        json=test_post_data,
        headers=verified_user["headers"]
    )
    post = response.json()
    
    return {
        **verified_user,
        "post": post
    }


@pytest_asyncio.fixture
async def post_with_comment(async_client, user_with_post, second_verified_user, test_comment_data):
    response = await async_client.post(
        f"/posts/{user_with_post['post']['id']}/comments",
        json=test_comment_data,
        headers=second_verified_user["headers"]
    )
    comment = response.json()
    
    return {
        "post_owner": user_with_post,
        "commenter": second_verified_user,
        "post": user_with_post["post"],
        "comment": comment
    }


@pytest_asyncio.fixture
async def old_unverified_user(async_client, db_session):
    user_data = {
        "email": "old@example.com",
        "username": "olduser",
        "full_name": "Old User",
        "password": "password123"
    }
    user_response = await register_user(async_client, user_data)
    
    from sqlalchemy import update
    old_time = datetime.now(timezone.utc) - timedelta(hours=72)
    await db_session.execute(
        update(User).where(User.email == user_data["email"]).values(created_at=old_time)
    )
    await db_session.commit()
    
    return {
        "user": user_response,
        "data": user_data
    }
