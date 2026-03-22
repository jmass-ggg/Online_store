from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, ConfigDict
from backend.models.cart import CartStauts
from uuid import UUID

class CartItemAdd(BaseModel):
    variant_id: UUID
    quantity: int = Field(default=1, ge=1)


class DecreaseQty(BaseModel):
    amount: int = Field(default=1, ge=1)


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cart_id: UUID
    variant_id: UUID
    quantity: int
    price: Decimal 


class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    buyer_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    subtotal: Decimal
    items: List[CartItemOut] = Field(default_factory=list)
