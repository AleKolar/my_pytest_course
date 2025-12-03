from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.shop_db import Model
from src.shop.cart.models.models_auth import User

if TYPE_CHECKING:
    from src.shop.cart.models.models_auth import User

class Cart(Model):
    __tablename__ = 'cart'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    price: Mapped[Decimal] = mapped_column(nullable=False)

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="cart_items")


    @property
    def total_price(self) -> Decimal:
        return Decimal(str(self.price)) * self.quantity

    def __repr__(self) -> str:
        return f"Cart(id={self.id}, item='{self.item}', user_id={self.user_id})"