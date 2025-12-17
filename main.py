from contextlib import asynccontextmanager
from typing import cast, Any
from datetime import datetime

import asyncpg
from fastapi import FastAPI, Depends
import uvicorn
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.database.config import DATABASE_URL
from src.database.shop_db import create_tables, get_db, engine
from src.shop.cart.endpoints.endpoints_auth import auth_router
from src.shop.cart.endpoints.endpoints_cart import cart_router
from src.shop.cart.models.models_auth import User


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Запуск приложение...")
    # Инициализируем engine SQLAlchemy
    app.state.db_engine = engine
    # Проверяем подключение к БД (опционально)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        print("✅ Подключение к БД успешно")
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        raise

    yield  # Работа приложения
    # Shutdown
    print("👋 Остановка приложения...")
    await engine.dispose()


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Жизненный цикл приложения"""
#     print("🚀 Запуск приложения...")
#     # Создаем таблицы
#     try:
#         await create_tables()
#     except Exception as e:
#         print(f"⚠️ Ошибка создания таблиц: {e}")
#         raise
#
#     yield
#
#     print("👋 Остановка приложения...")


app = FastAPI(
    title="Shop API",
    description="API для интернет-магазина",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    cast(Any, CORSMiddleware),
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(cart_router)


# ==================== БАЗОВЫЕ API ЭНДПОИНТЫ ====================
@app.get("/")
async def root():
    """Корневой эндпоинт для проверки работы API."""
    return {
        "message": "Shop API работает!",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Проверка состояния сервиса."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "shop-api"
    }

# ==================== АДМИНИСТРАТИВНЫЕ ЭНДПОИНТЫ ====================
@app.get("/admin/users")
async def get_all_users(
        db: AsyncSession = Depends(get_db)
    ):
    """Получение списка всех пользователей (только для админов)."""
    # Проверка прав (добавьте логику проверки ролей)
    result = await db.execute(select(User))
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in users
    ]


# ==================== КОНФИГУРАЦИЯ ДОКУМЕНТАЦИИ ====================
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    """Получение OpenAPI схемы."""
    return app.openapi()


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)

# uvicorn main:app --reload
# only port == 8001
