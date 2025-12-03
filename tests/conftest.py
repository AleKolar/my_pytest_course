import sys
from pathlib import Path
import pytest
import pytest_asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.shop.cart.models import Model


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
        yield session
        await session.rollback()