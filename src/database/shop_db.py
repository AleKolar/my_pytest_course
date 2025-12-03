"""
Подключение к PostgreSQL через asyncpg
"""
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncSession
)
from sqlalchemy.exc import SQLAlchemyError
from typing import AsyncGenerator
import logging

from sqlalchemy.orm import DeclarativeBase

from src.database.config import DATABASE_URL, DB_ECHO, DB_MAX_OVERFLOW, DB_POOL_SIZE

class Model(DeclarativeBase):
   pass


logger = logging.getLogger(__name__)

# Создаем engine для PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Проверяем соединение перед использованием
    pool_recycle=3600,   # Пересоздаем соединения каждые 3600 секунд

)

new_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.
    """
    session = new_session()
    try:
        yield session
    finally:
        await session.close()

async def create_tables():
    """
    Создает все таблицы в БД.
    Используется только для разработки/тестирования.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.create_all)
    logger.info("Tables created successfully")

async def delete_tables():
    """
    Удаляет все таблицы из БД (опасно!).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
    logger.warning("All tables deleted")