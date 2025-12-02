# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from src.database.shop_db import create_tables
from src.endpoints.endpoints_cart import cart_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    print("🚀 Запуск приложения...")

    # Создаем таблицы
    try:
        await create_tables()
    except Exception as e:
        print(f"⚠️ Ошибка создания таблиц: {e}")
        print("   Убедитесь, что:")
        print("   1. PostgreSQL запущен (docker-compose up -d)")
        raise

    yield

    print("👋 Остановка приложения...")


app = FastAPI(
    title="Магазин API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(cart_router)


@app.get("/")
def root():
    return {"message": "Магазин API работает!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
