from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from src.shop.cart.dependencies.dependencies_auth.dependencies import CurrentUser
from src.shop.cart.repository import CartRepository

from src.database.shop_db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from src.shop.cart.schemas.schemas_cart import CartInDB, CartCreate, CartUpdate

"""
Эндпоинты FastAPI для работы с корзиной покупок.
Теперь все операции привязаны к текущему пользователю.
"""

cart_router = APIRouter(prefix="/cart", tags=["cart"])


def get_cart_repository(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> CartRepository:
    """Создает экземпляр репозитория корзины."""
    return CartRepository(db)


@cart_router.post(
    "/",
    response_model=CartInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить товар в корзину"
)
async def create_cart_item(
    cart_item: CartCreate,
    current_user: CurrentUser,
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Добавить товар в корзину текущего пользователя.
    """
    try:
        created_item = await repository.create_cart_item(
            cart_item,
            current_user.id  # !!! Передаем ID пользователя
        )
        return created_item
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании товара: {str(e)}"
        )


@cart_router.get(
    "/",
    response_model=List[CartInDB],
    summary="Получить все товары в корзине"
)
async def get_cart_items(
    current_user: CurrentUser,  # !!! Теперь есть текущий пользователь со своей корзиной
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(100, ge=1, le=200, description="Максимальное количество записей"),
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Получить все товары в корзине текущего пользователя.
    """
    items = await repository.get_all_cart_items(
        current_user.id,  # !!! Передаем ID пользователя
        skip=skip,
        limit=limit
    )
    return items


@cart_router.get(
    "/{item_id}",
    response_model=CartInDB,
    summary="Получить товар по ID"
)
async def get_cart_item(
    item_id: int,
    current_user: CurrentUser,  # !!! Получаем текущего пользователя
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Получить товар из корзины текущего пользователя по ID.
    """
    cart_item = await repository.get_cart_item(item_id, current_user.id)

    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с ID {item_id} не найден"
        )

    return cart_item


@cart_router.patch(
    "/{item_id}",
    response_model=CartInDB,
    summary="Обновить товар в корзине"
)
async def update_cart_item(
    item_id: int,
    cart_update: CartUpdate,
    current_user: CurrentUser,  # !!! Получаем текущего пользователя
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Обновить товар в корзине текущего пользователя.
    """
    updated_item = await repository.update_cart_item(
        item_id,
        cart_update,
        current_user.id
    )

    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с ID {item_id} не найден"
        )

    return updated_item


@cart_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить товар из корзины"
)
async def delete_cart_item(
    item_id: int,
    current_user: CurrentUser,  # Получаем текущего пользователя
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Удалить товар из корзины текущего пользователя.
    """
    deleted = await repository.delete_cart_item(item_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с ID {item_id} не найден"
        )


@cart_router.delete(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Очистить всю корзину"
)
async def clear_cart(
    current_user: CurrentUser,  # Получаем текущего пользователя
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Очистить корзину текущего пользователя.
    """
    deleted_count = await repository.clear_cart(current_user.id)

    return {
        "message": f"Корзина очищена. Удалено товаров: {deleted_count}",
        "user_id": current_user.id
    }


@cart_router.get(
    "/summary/total",
    summary="Получить общую стоимость корзины"
)
async def get_cart_total(
    current_user: CurrentUser,  # Получаем текущего пользователя
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Получить общую стоимость корзины текущего пользователя.
    """
    total_price = await repository.get_cart_total_price(current_user.id)

    return {
        "user_id": current_user.id,
        "total_price": str(total_price)
    }


@cart_router.get(
    "/summary/full",
    summary="Получить полную сводку по корзине"
)
async def get_cart_full_summary(
    current_user: CurrentUser,  # Получаем текущего пользователя
    repository: CartRepository = Depends(get_cart_repository)
):
    """
    Получить полную сводку по корзине текущего пользователя.
    """
    summary = await repository.get_cart_summary(current_user.id)
    return summary