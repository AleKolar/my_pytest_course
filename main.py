from contextlib import asynccontextmanager
from typing import cast, Any, Annotated

from fastapi import FastAPI, Form, Depends, status
import uvicorn
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware
from fastapi import Request
from starlette.responses import HTMLResponse, JSONResponse

from src.database.shop_db import create_tables, get_db
from src.shop.cart import templates
from src.shop.cart.endpoints.endpoints_auth import auth_router
from src.shop.cart.endpoints.endpoints_cart import cart_router
from src.shop.cart.models.models_auth import User
from src.shop.cart.utils import create_access_token, verify_password, get_password_hash


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
    title="Shop API with Authentication",
    description="API для интернет-магазина с аутентификацией",
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

user_tokens = {}

app.include_router(auth_router)
app.include_router(cart_router)


# @app.get("/")
# def root():
#     return {"message": "Магазин API работает!"}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message": {
                "type": "info",
                "text": "Добро пожаловать в интернет-магазин!"
            }
        }
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа."""
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.post("/login")
async def login(
        request: Request,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
        db: Annotated[AsyncSession, Depends(get_db)]
):
    """Обработка входа через форму."""
    # Ищем пользователя
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Неверное имя пользователя или пароль"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Создаем токен
    access_token = create_access_token(data={"sub": user.username})

    # Сохраняем токен для пользователя (для веб-сессии)
    user_tokens[user.username] = access_token

    # Генерируем HTML-страницу с автоматическим сохранением токена
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Успешный вход</title>
        <script>
            // Сохраняем токен в localStorage
            localStorage.setItem('auth_token', '{access_token}');
            // Перенаправляем на главную
            window.location.href = '/';
        </script>
    </head>
    <body>
        <p>Вход выполнен успешно! Перенаправление...</p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Страница регистрации."""
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@app.post("/register")
async def register(
        request: Request,
        username: Annotated[str, Form()],
        email: Annotated[str, Form()],
        password: Annotated[str, Form()],
        password_confirm: Annotated[str, Form()],
        db: Annotated[AsyncSession, Depends(get_db)]
):
    """Обработка регистрации через форму."""
    # Проверяем пароли
    if password != password_confirm:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пароли не совпадают"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Проверяем, не существует ли уже пользователь
    result = await db.execute(
        select(User).where(User.username == username)
    )
    if result.scalar_one_or_none():
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пользователь с таким именем уже существует"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Проверяем email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    if result.scalar_one_or_none():
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Пользователь с таким email уже существует"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Создаем пользователя
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Сразу логиним пользователя
    access_token = create_access_token(data={"sub": new_user.username})
    user_tokens[new_user.username] = access_token

    # HTML с автоматическим сохранением токена
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Успешная регистрация</title>
        <script>
            // Сохраняем токен в localStorage
            localStorage.setItem('auth_token', '{access_token}');
            // Перенаправляем на главную
            window.location.href = '/';
        </script>
    </head>
    <body>
        <p>Регистрация успешна! Перенаправление...</p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.get("/logout")
async def logout():
    """Выход из системы."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Выход</title>
        <script>
            // Удаляем токен из localStorage
            localStorage.removeItem('auth_token');
            // Перенаправляем на главную
            window.location.href = '/';
        </script>
    </head>
    <body>
        <p>Выход выполнен! Перенаправление...</p>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


# Обновляем index.html для отображения статуса
@app.get("/status", response_class=JSONResponse)
async def get_status(request: Request):
    """Проверка статуса авторизации."""
    # Проверяем есть ли токен в заголовке
    auth_header = request.headers.get("Authorization")
    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]

    return {
        "has_token": token is not None,
        "auth_header": auth_header
    }



""" =============== Swagger для автоматического использования токена ============= """

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    """Кастомная страница Swagger с автоподстановкой токена."""
    root_path = request.scope.get("root_path", "").rstrip("/")

    return get_swagger_ui_html(
        openapi_url=f"{root_path}/openapi.json",
        title=app.title + " - Swagger UI",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "tryItOutEnabled": True,
        }
    )


@app.middleware("http")
async def add_token_to_swagger(request: Request, call_next):
    """Middleware для автоподстановки токена в Swagger."""
    if request.url.path == "/docs" and "token" in request.query_params:
        # Если есть токен в параметрах, добавляем его в cookies для Swagger
        token = request.query_params.get("token")
        response = await call_next(request)

        # Устанавливаем токен в localStorage через JavaScript
        html = response.body.decode()
        if token and 'localStorage.setItem' not in html:
            script = f"""
            <script>
                if (!localStorage.getItem('auth_token')) {{
                    localStorage.setItem('auth_token', '{token}');
                }}
                // Автоматически заполняем поле токена в Swagger
                window.onload = function() {{
                    setTimeout(function() {{
                        const authBtn = document.querySelector('.btn.authorize');
                        if (authBtn) {{
                            authBtn.click();
                            setTimeout(function() {{
                                const tokenInput = document.querySelector('input[placeholder*="apiKey"]');
                                if (tokenInput) {{
                                    tokenInput.value = 'Bearer {token}';
                                    const modal = document.querySelector('.dialog-ux');
                                    if (modal) {{
                                        const closeBtn = modal.querySelector('.close-modal');
                                        if (closeBtn) closeBtn.click();
                                    }}
                                }}
                            }}, 500);
                        }}
                    }}, 1000);
                }};
            </script>
            """
            html = html.replace('</body>', script + '</body>')
            return HTMLResponse(content=html)

    return await call_next(request)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# python uvicorn main^app --reload
