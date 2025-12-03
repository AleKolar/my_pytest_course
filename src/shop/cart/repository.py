from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.shop.cart.models.models_cart import Cart
from src.shop.cart.schemas.schemas_cart import CartCreate, CartUpdate


class CartRepository:
    """Репозиторий для работы с корзиной."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_cart_item(self, cart_data: CartCreate, user_id: int) -> Cart:
        """
        Создает новый элемент корзины для конкретного пользователя.
        """
        cart_item = Cart(
            item=cart_data.item,
            quantity=cart_data.quantity,
            price=cart_data.price,
            user_id=user_id  # !!! Добавляем user_id конкретного пользователя с конкретной корзиной
        )

        self.session.add(cart_item)
        await self.session.flush()
        await self.session.refresh(cart_item)

        return cart_item

    async def get_cart_item(self, item_id: int, user_id: int) -> Optional[Cart]:
        """
        Получает элемент корзины по ID для конкретного пользователя.
        """
        result = await self.session.execute(
            select(Cart)
            .where(Cart.id == item_id)
            .where(Cart.user_id == user_id)  # Фильтруем по пользователю
        )
        return result.scalar_one_or_none()

    async def get_all_cart_items(
            self,
            user_id: int,  # Добавляем user_id
            skip: int = 0,
            limit: int = 100
    ) -> List[Cart]:
        """
        Получает все элементы корзины пользователя.
        """
        result = await self.session.execute(
            select(Cart)
            .where(Cart.user_id == user_id)  # Фильтруем по пользователю
            .offset(skip)
            .limit(limit)
            .order_by(Cart.created_at.desc())
        )
        return result.scalars().all()

    async def update_cart_item(
            self,
            item_id: int,
            cart_update: CartUpdate,
            user_id: int  # Добавляем user_id
    ) -> Optional[Cart]:
        """
        Обновляет элемент корзины пользователя.
        """
        # Получаем элемент из БД с проверкой user_id
        cart_item = await self.get_cart_item(item_id, user_id)
        if not cart_item:
            return None

        update_data = cart_update.model_dump(exclude_unset=True)

        await self.session.execute(
            update(Cart)
            .where(Cart.id == item_id)
            .where(Cart.user_id == user_id)  # Фильтруем по пользователю
            .values(**update_data)
        )

        await self.session.flush()
        await self.session.refresh(cart_item)

        return cart_item

    async def delete_cart_item(self, item_id: int, user_id: int) -> bool:
        """
        Удаляет элемент корзины пользователя.
        """
        cart_item = await self.get_cart_item(item_id, user_id)
        if not cart_item:
            return False

        await self.session.delete(cart_item)
        await self.session.flush()

        return True

    async def clear_cart(self, user_id: int) -> int:
        """
        Очищает корзину пользователя.
        """
        result = await self.session.execute(
            delete(Cart)
            .where(Cart.user_id == user_id)  # Фильтруем по пользователю
        )
        await self.session.flush()

        return result.rowcount or 0

    async def get_cart_total_price(self, user_id: int) -> Decimal:
        """
        Рассчитывает общую стоимость корзины пользователя.
        """
        result = await self.session.execute(
            select(Cart)
            .where(Cart.user_id == user_id)  # Фильтруем по пользователю
        )
        cart_items = result.scalars().all()

        total = Decimal('0')
        for item in cart_items:
            total += item.total_price

        return total

    async def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Возвращает сводку по корзине пользователя.
        """
        cart_items = await self.get_all_cart_items(user_id)
        total_price = await self.get_cart_total_price(user_id)

        return {
            "total_items": len(cart_items),
            "total_price": str(total_price),
            "user_id": user_id,
            "items": [
                {
                    "id": item.id,
                    "item": item.item,
                    "quantity": item.quantity,
                    "price": str(item.price),
                    "total_price": str(item.total_price)
                }
                for item in cart_items
            ]
        }
