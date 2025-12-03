import pytest
import pytest_asyncio
from decimal import Decimal

from src.shop.cart.repository import CartRepository
from src.shop.cart.schemas.schemas_cart import CartCreate



class ShoppingCart:
    def __init__(self, session, user_id: int):
        self.repo = CartRepository(session)
        self.user_id = user_id

    async def add_item(self, item_name: str, price: float):
        cart_data = CartCreate(
            item=item_name,
            quantity=1,
            price=Decimal(str(price))
        )
        return await self.repo.create_cart_item(cart_data, self.user_id)

    async def get_total_price(self):
        return await self.repo.get_cart_total_price(self.user_id)

    async def get_all_items(self):
        return await self.repo.get_all_cart_items(self.user_id)

    async def delete_item(self, item_id: int):
        return await self.repo.delete_cart_item(item_id, self.user_id)


@pytest_asyncio.fixture
async def empty_cart(db_session, test_user_id):
    return ShoppingCart(db_session, user_id=test_user_id)


@pytest_asyncio.fixture
async def filled_cart(empty_cart):
    await empty_cart.add_item("apple", 10.0)
    await empty_cart.add_item("banana", 20.0)
    return empty_cart


@pytest.mark.asyncio
async def test_add_item_to_empty_cart(empty_cart):
    await empty_cart.add_item("cherry", 30.0)
    all_items = await empty_cart.get_all_items()
    item_names = [item.item for item in all_items]
    assert "cherry" in item_names


@pytest.mark.asyncio
async def test_get_total_price_of_empty_cart(empty_cart):
    total = await empty_cart.get_total_price()
    assert total == Decimal("0")


@pytest.mark.asyncio
async def test_add_item_to_filled_cart(filled_cart):
    await filled_cart.add_item("cherry", 30.0)
    all_items = await filled_cart.get_all_items()
    item_names = [item.item for item in all_items]
    assert "cherry" in item_names


@pytest.mark.asyncio
async def test_get_total_price_of_filled_cart(filled_cart):
    total = await filled_cart.get_total_price()
    assert total == Decimal("30.0")


# pytest tests/test_cart_fixture.py -v --html=report.html