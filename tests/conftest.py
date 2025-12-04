import sys
from pathlib import Path
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shop.cart.endpoints.endpoints_auth import auth_router
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.shop_db import Model
from src.shop.cart.models.models_auth import User
from src.shop.cart.utils import get_password_hash
from src.shop.cart.models.models_cart import Cart

# Тестовая БД (SQLite в памяти)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def engine():
    """Создает тестовый движок БД."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Создает тестовую сессию БД."""
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session):
    """Создает и возвращает тестового пользователя."""
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword")
    )
    db_session.add(test_user)
    await db_session.commit()
    await db_session.refresh(test_user)
    return test_user

@pytest_asyncio.fixture
async def test_user_id(test_user):
    """Возвращает ID тестового пользователя."""
    return test_user.id


@pytest_asyncio.fixture
def app(engine):
    """Создает тестовое приложение FastAPI."""
    from fastapi import FastAPI
    from src.database.shop_db import get_db

    app = FastAPI()

    # Включаем роутер
    app.include_router(auth_router)

    # Создаем таблицы
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Model.metadata.create_all)

    import asyncio
    asyncio.run(create_tables())

    # Переопределяем зависимость get_db
    async def override_get_db():
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    return app



@pytest_asyncio.fixture
async def async_client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

