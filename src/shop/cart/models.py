from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Model(DeclarativeBase):
   pass


class Cart(Model):
    __tablename__ = 'cart'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    price: Mapped[Decimal] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    @property
    def total_price(self) -> Decimal:
        return Decimal(str(self.price)) * self.quantity

    def __repr__(self) -> str:
        return f"Cart(id={self.id}, item='{self.item}', quantity={self.quantity}, price={self.price})"