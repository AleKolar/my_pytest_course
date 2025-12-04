import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    """Тест успешной регистрации пользователя"""
    # Тестовые данные
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
    }

    # Отправляем запрос на регистрацию
    response = await async_client.post("/auth/register", json=user_data)

    # Проверяем ответ
    assert response.status_code == 201
    data = response.json()

    # Проверяем данные в ответе
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "is_active" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(async_client: AsyncClient):
    """Тест регистрации с уже существующим username"""
    # Сначала регистрируем пользователя
    user_data = {
        "username": "duplicateuser",
        "email": "duplicate@example.com",
        "password": "password123"
    }

    response = await async_client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Пытаемся зарегистрировать с тем же username
    duplicate_data = {
        "username": "duplicateuser",
        "email": "different@example.com",
        "password": "password456"
    }

    response = await async_client.post("/auth/register", json=duplicate_data)

    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    """Тест регистрации с уже существующим email"""
    # Сначала регистрируем пользователя
    user_data = {
        "username": "user1",
        "email": "duplicate@example.com",
        "password": "password123"
    }

    response = await async_client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Пытаемся зарегистрировать с тем же email
    duplicate_data = {
        "username": "user2",
        "email": "duplicate@example.com",
        "password": "password456"
    }

    response = await async_client.post("/auth/register", json=duplicate_data)

    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_data(async_client: AsyncClient):
    """Тест регистрации с невалидными данными"""
    # Неполные данные
    invalid_data = {
        "username": "ab",  # Слишком короткий username
        "email": "invalid-email",  # Невалидный email
        "password": "123"  # Слишком короткий пароль
    }

    response = await async_client.post("/auth/register", json=invalid_data)

    assert response.status_code == 422  # Unprocessable Entity - Это Pydantic


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Тест успешного входа в систему"""
    # Сначала регистрируем пользователя
    user_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "testpassword123"
    }

    register_response = await async_client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Теперь логинимся
    form_data = {
        "username": "loginuser",
        "password": "testpassword123"
    }

    response = await async_client.post(
        "/auth/login",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    """Тест входа с неверным паролем"""
    # Сначала регистрируем пользователя
    user_data = {
        "username": "wrongpassuser",
        "email": "wrongpass@example.com",
        "password": "correctpassword"
    }

    register_response = await async_client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Пытаемся войти с неправильным паролем
    form_data = {
        "username": "wrongpassuser",
        "password": "wrongpassword"
    }

    response = await async_client.post(
        "/auth/login",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Тест входа с несуществующим пользователем"""
    form_data = {
        "username": "nonexistent",
        "password": "password123"
    }

    response = await async_client.post(
        "/auth/login",
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_success(async_client: AsyncClient):
    """Тест получения информации о текущем пользователе"""
    # Сначала регистрируем пользователя
    user_data = {
        "username": "authuser",
        "email": "auth@example.com",
        "password": "testpass"
    }

    register_response = await async_client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Логинимся
    login_data = {
        "username": "authuser",
        "password": "testpass"
    }

    login_response = await async_client.post(
        "/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    token = login_response.json()["access_token"]

    # Теперь запрашиваем информацию о пользователе
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "authuser"
    assert data["email"] == "auth@example.com"
    assert "id" in data
    assert "is_active" in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(async_client: AsyncClient):
    """Тест получения информации о пользователе без токена"""
    response = await async_client.get("/auth/me")

    assert response.status_code == 401  # Unauthorized
    assert "Not authenticated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(async_client: AsyncClient):
    """Тест получения информации о пользователе с невалидным токеном"""
    response = await async_client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient):
    """Тест обновления токена"""
    # Сначала регистрируем пользователя
    user_data = {
        "username": "refreshuser",
        "email": "refresh@example.com",
        "password": "testpass"
    }

    register_response = await async_client.post("/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Логинимся
    login_data = {
        "username": "refreshuser",
        "password": "testpass"
    }

    login_response = await async_client.post(
        "/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    old_token = login_response.json()["access_token"]

    # Обновляем токен
    response = await async_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {old_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_full_flow(async_client: AsyncClient):
    """Тест полного цикла: регистрация -> логин -> получение данных -> обновление токена"""
    # 1. Регистрация
    register_data = {
        "username": "flowuser",
        "email": "flow@example.com",
        "password": "flowpassword123"
    }

    register_response = await async_client.post("/auth/register", json=register_data)
    assert register_response.status_code == 201

    # 2. Логин
    login_response = await async_client.post(
        "/auth/login",
        data={"username": "flowuser", "password": "flowpassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. Получение данных пользователя
    me_response = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == "flowuser"
    assert user_data["email"] == "flow@example.com"

    # 4. Обновление токена
    refresh_response = await async_client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert refresh_response.status_code == 200
    new_token = refresh_response.json()["access_token"]

    # 5. Проверяем, что новый токен работает
    me_response2 = await async_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {new_token}"}
    )
    assert me_response2.status_code == 200



# pytest tests/test_client.py -v --html=report.html