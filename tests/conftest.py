import sys
from pathlib import Path
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shop.cart.endpoints.endpoints_auth import auth_router
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.shop_db import Model, get_db
from src.shop.cart.models.models_auth import User
from src.shop.cart.utils import get_password_hash

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """Создает тестовый движок БД."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)

    yield engine

    # Очищаем и закрываем движок
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
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
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Создает и возвращает тестового пользователя."""
    test_user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
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

    app = FastAPI()

    # Включаем роутер
    app.include_router(auth_router)

    # Переопределяем зависимость get_db
    async def override_get_db():
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with async_session() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    return app


@pytest_asyncio.fixture
async def async_client(app):
    """Создает асинхронный тестовый клиент."""
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def authenticated_client(async_client, test_user):
    """Создает аутентифицированный тестовый клиент."""
    # Логинимся для получения токена
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    token = login_response.json()["access_token"]

    # Возвращаем клиент с заголовком авторизации
    async_client.headers.update({"Authorization": f"Bearer {token}"})
    return async_client


# Фикстура для очистки БД между тестами
@pytest_asyncio.fixture(autouse=True)
async def clean_db(engine, db_session):
    """Автоматически очищает базу данных перед каждым тестом."""
    # Очищаем все таблицы
    for table in reversed(Model.metadata.sorted_tables):
        await db_session.execute(table.delete())
    await db_session.commit()
    yield

