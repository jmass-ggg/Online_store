from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, ConfigDict
from backend.models.cart import CartStauts


class CartItemAdd(BaseModel):
    variant_id: int
    quantity: int = Field(default=1, ge=1)


class DecreaseQty(BaseModel):
    amount: int = Field(default=1, ge=1)


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cart_id: int
    variant_id: int
    quantity: int
    price: Decimal 


class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buyer_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    subtotal: Decimal
    items: List[CartItemOut] = Field(default_factory=list)
