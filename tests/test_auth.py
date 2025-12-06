import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.shop.cart.models.models_auth import User
from src.shop.cart.models.models_cart import Cart


@pytest.mark.asyncio
class TestAuthIntegration:
    """Интеграционные тесты для модуля аутентификации"""

    async def test_register_user_success(self, async_client: AsyncClient, db_session: AsyncSession):
        """Тест успешной регистрации пользователя"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }

        response = await async_client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data

        # Проверяем запись в БД
        result = await db_session.execute(
            select(User).where(User.username == user_data["username"])
        )
        db_user = result.scalar_one_or_none()

        assert db_user is not None
        assert db_user.email == user_data["email"]
        assert db_user.is_active == True

    async def test_register_duplicate_username(self, async_client: AsyncClient, test_user: User):
        """Тест регистрации с уже существующим именем пользователя"""
        user_data = {
            "username": "testuser",  # Такой же как у test_user
            "email": "different@example.com",
            "password": "password123"
        }

        response = await async_client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already registered" in response.json()["detail"]

    async def test_register_duplicate_email(self, async_client: AsyncClient, test_user: User):
        """Тест регистрации с уже существующим email"""
        user_data = {
            "username": "differentuser",
            "email": "test@example.com",  # Такой же как у test_user
            "password": "password123"
        }

        response = await async_client.post("/auth/register", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    async def test_login_success(self, async_client: AsyncClient, test_user: User):
        """Тест успешного входа в систему"""
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }

        response = await async_client.post(
            "/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(self, async_client: AsyncClient, test_user: User):
        """Тест входа с неправильным паролем"""
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        response = await async_client.post(
            "/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        """Тест входа несуществующего пользователя"""
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }

        response = await async_client.post(
            "/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    async def test_get_current_user_authenticated(self, authenticated_client: AsyncClient):
        """Тест получения информации о текущем пользователе с авторизацией"""
        response = await authenticated_client.get("/auth/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "is_active" in data
        assert data["is_active"] == True

    async def test_get_current_user_unauthenticated(self, async_client: AsyncClient):
        """Тест получения информации о текущем пользователе без авторизации"""
        response = await async_client.get("/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_refresh_token(self, authenticated_client: AsyncClient):
        """Тест обновления токена"""
        response = await authenticated_client.post("/auth/refresh")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
class TestCRUDOperations:
    """Тесты CRUD операций через API"""

    async def test_user_lifecycle(self, async_client: AsyncClient, db_session: AsyncSession):
        """Полный цикл жизни пользователя через API"""
        # 1. CREATE - Регистрация пользователя
        user_data = {
            "username": "lifecycleuser",
            "email": "lifecycle@example.com",
            "password": "lifecyclepass123"
        }

        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        user_id = register_response.json()["id"]

        # 2. READ (неавторизованный) - должен быть отказ
        me_response = await async_client.get("/auth/me")
        assert me_response.status_code == status.HTTP_401_UNAUTHORIZED

        # 3. Аутентификация (получение токена)
        login_response = await async_client.post(
            "/auth/login",
            data={"username": "lifecycleuser", "password": "lifecyclepass123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # 4. READ (авторизованный) - получение информации
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await async_client.get("/auth/me", headers=headers)
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["username"] == "lifecycleuser"

        # 5. UPDATE (косвенное) - обновление токена
        refresh_response = await async_client.post("/auth/refresh", headers=headers)
        assert refresh_response.status_code == status.HTTP_200_OK

        # Проверяем, что пользователь создан в БД
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.username == "lifecycleuser"

    async def test_multiple_users_registration(self, async_client: AsyncClient, db_session: AsyncSession):
        """Тест регистрации нескольких пользователей"""
        users_data = [
            {"username": "user1", "email": "user1@example.com", "password": "pass123456"},
            {"username": "user2", "email": "user2@example.com", "password": "pass654321"},
            {"username": "user3", "email": "user3@example.com", "password": "pass987654"},
        ]

        for user_data in users_data:
            response = await async_client.post("/auth/register", json=user_data)
            assert response.status_code == status.HTTP_201_CREATED

        # Проверяем, что все пользователи созданы в БД
        result = await db_session.execute(select(User))
        users = result.scalars().all()

        usernames = [user.username for user in users]
        for user_data in users_data:
            assert user_data["username"] in usernames


@pytest.mark.parametrize("user_data, expected_status", [
    # Валидные данные
    (
            {"username": "validuser", "email": "test@example.com", "password": "password123"},
            status.HTTP_201_CREATED
    ),
    # Невалидный username (слишком короткий)
    (
            {"username": "ab", "email": "test@example.com", "password": "password123"},
            status.HTTP_422_UNPROCESSABLE_ENTITY
    ),
    # Невалидный email
    (
            {"username": "validuser", "email": "invalid-email", "password": "password123"},
            status.HTTP_422_UNPROCESSABLE_ENTITY
    ),
    # Невалидный пароль (слишком короткий)
    (
            {"username": "validuser", "email": "test@example.com", "password": "123"},
            status.HTTP_422_UNPROCESSABLE_ENTITY
    ),
    # Невалидный пароль (слишком длинный)
    (
            {"username": "validuser", "email": "test@example.com", "password": "a" * 30},
            status.HTTP_422_UNPROCESSABLE_ENTITY
    ),
])
@pytest.mark.asyncio
async def test_register_validation_parameterized(async_client: AsyncClient, user_data, expected_status):
    """Параметризованный тест валидации регистрации"""
    response = await async_client.post("/auth/register", json=user_data)
    assert response.status_code == expected_status


@pytest.mark.asyncio
class TestErrorScenarios:
    """Тесты сценариев ошибок"""

    async def test_invalid_token_format(self, async_client: AsyncClient):
        """Тест с неверным форматом токена"""
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": "InvalidTokenFormat"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_malformed_token(self, async_client: AsyncClient):
        """Тест с некорректным токеном"""
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer malformed.token.here"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_concurrent_registration(async_client: AsyncClient, db_session: AsyncSession):
    """Тест конкурентной регистрации пользователей"""
    import asyncio

    async def register_user(username, email, password):
        user_data = {"username": username, "email": email, "password": password}
        response = await async_client.post("/auth/register", json=user_data)
        return response.status_code

    # Создаем задачи для конкурентной регистрации
    tasks = []
    for i in range(3):
        tasks.append(register_user(
            f"concurrent{i}",
            f"concurrent{i}@example.com",
            f"password{i}"
        ))

    results = await asyncio.gather(*tasks)

    # Все регистрации должны быть успешными
    for result in results:
        assert result == status.HTTP_201_CREATED

    # Проверяем, что все пользователи созданы
    result = await db_session.execute(select(User))
    users = result.scalars().all()
    usernames = [user.username for user in users]

    for i in range(3):
        assert f"concurrent{i}" in usernames



# pytest tests/test_auth.py -v --html=report.html
# pytest tests/test_auth.py -v