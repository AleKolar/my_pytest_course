from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.shop.cart.models import Cart
from src.shop.cart.schemas import CartCreate, CartUpdate


class CartRepository:
    """Репозиторий для работы с корзиной."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_cart_item(self, cart_data: CartCreate) -> Cart:
        """
        Создает новый элемент корзины.

        Args:
            cart_data: Данные для создания элемента корзины

        Returns:
            Созданный объект Cart
        """
        ''' Создаем объект Cart из Pydantic схемы '''
        cart_item = Cart(
            item=cart_data.item,
            quantity=cart_data.quantity,
            price=cart_data.price
        )

        self.session.add(cart_item)
        await self.session.flush()
        await self.session.refresh(cart_item)

        return cart_item

    async def get_cart_item(self, item_id: int) -> Optional[Cart]:
        """
        Получает элемент корзины по ID.

        Args:
            item_id: ID элемента корзины

        Returns:
            Объект Cart или None, если не найден
        """
        result = await self.session.execute(
            select(Cart).where(Cart.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_all_cart_items(
            self,
            skip: int = 0,
            limit: int = 100
    ) -> List[Cart]:
        """
        Получает все элементы корзины с пагинацией.

        Args:
            skip: Количество элементов для пропуска
            limit: Максимальное количество элементов

        Returns:
            Список объектов Cart
        """
        result = await self.session.execute(
            select(Cart)
            .offset(skip)
            .limit(limit)
            .order_by(Cart.created_at.desc())
        )
        return result.scalars().all()

    async def update_cart_item(
            self,
            item_id: int,
            cart_update: CartUpdate
    ) -> Optional[Cart]:
        """
        Обновляет элемент корзины.

        Args:
            item_id: ID элемента для обновления
            cart_update: Данные для обновления

        Returns:
            Обновленный объект Cart или None, если не найден
        """
        # Получаем элемент
        cart_item = await self.get_cart_item(item_id)
        if not cart_item:
            return None

        # Подготавливаем данные для обновления
        update_data = cart_update.model_dump(exclude_unset=True)

        ''' Выполняем обновление '''
        await self.session.execute(
            update(Cart)
            .where(Cart.id == item_id)
            .values(**update_data)
        )

        await self.session.flush()
        await self.session.refresh(cart_item)

        return cart_item

    async def delete_cart_item(self, item_id: int) -> bool:
        """
        Удаляет элемент корзины.

        Args:
            item_id: ID элемента для удаления

        Returns:
            True, если элемент удален, False если не найден
        """
        # Проверяем существование элемента
        cart_item = await self.get_cart_item(item_id)
        if not cart_item:
            return False

        ''' Удаляем элемент '''
        await self.session.delete(cart_item)
        await self.session.flush()

        return True

    async def clear_cart(self) -> int:
        """
        Очищает всю корзину.

        Returns:
            Количество удаленных элементов
        """
        result = await self.session.execute(
            delete(Cart)
        )
        await self.session.flush()

        return result.rowcount or 0

    async def get_cart_total_price(self) -> Decimal:
        """
        Рассчитывает общую стоимость всех товаров в корзине.

        Returns:
            Общая стоимость
        """
        result = await self.session.execute(
            select(Cart)
        )
        cart_items = result.scalars().all()

        total = Decimal('0')
        for item in cart_items:
            total += item.total_price

        return total

    async def get_cart_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку по корзине.

        Returns:
            Словарь с информацией о корзине
        """
        cart_items = await self.get_all_cart_items()
        total_price = await self.get_cart_total_price()

        return {
            "total_items": len(cart_items),
            "total_price": str(total_price),
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

