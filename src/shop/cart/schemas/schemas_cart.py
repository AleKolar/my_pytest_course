from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class CartBase(BaseModel):
    item: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(1, ge=1, le=1000)
    price: Decimal = Field(..., ge=0)


class CartCreate(CartBase):
    pass


class CartUpdate(BaseModel):
    quantity: int | None = Field(None, ge=1, le=1000)
    price: Decimal | None = Field(None, ge=0)


class CartInDB(CartBase):
    id: int
    total_price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)