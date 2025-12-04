from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from src.database.shop_db import get_db
from src.shop.cart.dependencies.dependencies_auth.dependencies import get_current_user, CurrentUser
from src.shop.cart.models.models_auth import User
from src.shop.cart.schemas.schemas_auth import UserInDB, UserCreate, Token
from src.shop.cart.utils import get_password_hash, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

auth_router = APIRouter(prefix="/auth", tags=["authentication"])


@auth_router.post(
    "/register",
    response_model=UserInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя"
)
async def register(
        user_data: UserCreate,
        db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Регистрация нового пользователя.

    - **username**: Имя пользователя (3-50 символов)
    - **email**: Email пользователя
    - **password**: Пароль (минимум 6 символов)
    """
    # Проверяем, не существует ли уже пользователь с таким username
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Проверяем, не существует ли уже пользователь с таким email
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Создаем нового пользователя
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@auth_router.post(
    "/login",
    response_model=Token,
    summary="Вход в систему"
)
async def login(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Вход в систему.

    - **username**: Имя пользователя
    - **password**: Пароль
    """
    # Ищем пользователя
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Проверяем пользователя и пароль
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем активен ли пользователь
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Создаем токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/refresh")
async def refresh_token(
        current_user: CurrentUser
):
    """Обновление токена."""
    access_token = create_access_token(
        data={"sub": current_user.username}
    )

    return Token(
        access_token=access_token,
        token_type="bearer"
    )

@auth_router.get(
    "/me",
    response_model=UserInDB,
    summary="Получить информацию о текущем пользователе"
)
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_user)]
):
    """Получить информацию о текущем пользователе."""
    return current_user