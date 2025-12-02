from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List


from src.database.shop_db import create_tables, get_db
from src.shop.cart.repository import CartRepository
from src.shop.cart.schemas import CartInDB, CartCreate, CartUpdate

"""
Эндпоинты FastAPI для работы с корзиной покупок.
"""

cart_router = APIRouter(prefix="/cart", tags=["cart"])

@cart_router.post(
   "/",
   response_model=CartInDB,
   status_code=status.HTTP_201_CREATED,
   summary="Добавить товар в корзину",
   description="Добавляет новый товар в корзину покупок"
)
async def create_cart_item(
        cart_item: CartCreate,
        db: AsyncSession = Depends(get_db)
):
   """
   Добавить товар в корзину.

   - **item**: Название товара (1-100 символов)
   - **quantity**: Количество товара (от 1 до 1000)
   - **price**: Цена товара (больше или равно 0)
   """
   cart_repo = CartRepository(db)
   try:
      created_item = await cart_repo.create_cart_item(cart_item)
      return created_item
   except Exception as e:
      raise HTTPException(
         status_code=status.HTTP_400_BAD_REQUEST,
         detail=f"Ошибка при создании товара: {str(e)}"
      )


@cart_router.get(
   "/",
   response_model=List[CartInDB],
   summary="Получить все товары в корзине",
   description="Возвращает список всех товаров в корзине с пагинацией"
)
async def get_cart_items(
        skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
        limit: int = Query(100, ge=1, le=200, description="Максимальное количество записей"),
        db: AsyncSession = Depends(get_db)
):
   """
   Получить все товары в корзине.

   - **skip**: Сколько записей пропустить (по умолчанию 0)
   - **limit**: Сколько записей вернуть (по умолчанию 100, максимум 200)
   """
   cart_repo = CartRepository(db)
   items = await cart_repo.get_all_cart_items(skip=skip, limit=limit)
   return items


@cart_router.get(
   "/{item_id}",
   response_model=CartInDB,
   summary="Получить товар по ID",
   description="Возвращает товар из корзины по его ID"
)
async def get_cart_item(
        item_id: int,
        db: AsyncSession = Depends(get_db)
):
   """
   Получить товар по ID.

   - **item_id**: ID товара в корзине
   """
   cart_repo = CartRepository(db)
   cart_item = await cart_repo.get_cart_item(item_id)

   if not cart_item:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail=f"Товар с ID {item_id} не найден"
      )

   return cart_item


@cart_router.put(
   "/{item_id}",
   response_model=CartInDB,
   summary="Обновить товар в корзине",
   description="Обновляет информацию о товаре в корзине"
)
async def update_cart_item(
        item_id: int,
        cart_update: CartUpdate,
        db: AsyncSession = Depends(get_db)
):
   """
   Обновить товар в корзине.

   - **item_id**: ID товара для обновления
   - **quantity**: Новое количество товара (опционально)
   - **price**: Новая цена товара (опционально)
   """
   cart_repo = CartRepository(db)
   updated_item = await cart_repo.update_cart_item(item_id, cart_update)

   if not updated_item:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail=f"Товар с ID {item_id} не найден"
      )

   return updated_item


@cart_router.delete(
   "/{item_id}",
   status_code=status.HTTP_204_NO_CONTENT,
   summary="Удалить товар из корзины",
   description="Удаляет товар из корзины по его ID"
)
async def delete_cart_item(
        item_id: int,
        db: AsyncSession = Depends(get_db)
):
   """
   Удалить товар из корзины.

   - **item_id**: ID товара для удаления
   """
   cart_repo = CartRepository(db)
   deleted = await cart_repo.delete_cart_item(item_id)

   if not deleted:
      raise HTTPException(
         status_code=status.HTTP_404_NOT_FOUND,
         detail=f"Товар с ID {item_id} не найден"
      )


@cart_router.delete(
   "/",
   status_code=status.HTTP_200_OK,
   summary="Очистить всю корзину",
   description="Удаляет все товары из корзины"
)
async def clear_cart(
        db: AsyncSession = Depends(get_db)
):
   """
   Очистить всю корзину.
   """
   cart_repo = CartRepository(db)
   deleted_count = await cart_repo.clear_cart()

   return {
      "message": f"Корзина очищена. Удалено товаров: {deleted_count}"
   }


@cart_router.get(
   "/summary/total",
   summary="Получить общую стоимость корзины",
   description="Возвращает общую стоимость всех товаров в корзине"
)
async def get_cart_total(
        db: AsyncSession = Depends(get_db)
):
   """
   Получить общую стоимость корзины.
   """
   cart_repo = CartRepository(db)
   total_price = await cart_repo.get_cart_total_price()

   return {
      "total_price": str(total_price)
   }


@cart_router.get(
   "/summary/full",
   summary="Получить полную сводку по корзине",
   description="Возвращает полную информацию о корзине"
)
async def get_cart_full_summary(
        db: AsyncSession = Depends(get_db)
):
   """
   Получить полную сводку по корзине.

   Включает:
   - Общее количество товаров
   - Общую стоимость
   - Детальную информацию по каждому товару
   """
   cart_repo = CartRepository(db)
   summary = await cart_repo.get_cart_summary()

   return summary

