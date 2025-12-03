import sys
from pathlib import Path
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import StaticPool, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.database.shop_db import Model
from src.shop.cart.models.models_auth import User


# Тестовая БД (SQLite в памяти)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def engine():
    """Создает тестовый движок БД."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool  # Важно для SQLite
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
        # !!! Здесь создаем тестового пользователя
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="fake_hashed_password"
        )
        session.add(test_user)
        await session.commit()
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def test_user(db_session):
    """Создает и возвращает тестового пользователя."""
    result = await db_session.execute(
        select(User).where(User.username == "testuser")
    )
    user = result.scalar_one()
    return user

@pytest_asyncio.fixture
async def test_user_id(test_user):
    """Возвращает ID тестового пользователя."""
    return test_user.id