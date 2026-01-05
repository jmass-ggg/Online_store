from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.models.cart import CartStauts

class CartItemCreate(BaseModel):
    variant_id: int
    quantity: int = Field(default=1, ge=1)

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)

class CartItemAdd(BaseModel):
    variant_id: int
    quantity: int = Field(default=1, ge=1)

class DecreaseQty(BaseModel):
    amount: int = Field(default=1, ge=1)

class CartItemOut(BaseModel):
    id: int
    cart_id: int
    variant_id: int
    quantity: int
    class Config:
        orm_mode = True
        from_attributes = True

class CartCreate(BaseModel):
    buyer_id: int
    status: CartStauts = CartStauts.ACTIVE

class CartOut(BaseModel):
    id: int
    buyer_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[CartItemOut] = []
    class Config:
        orm_mode = True
        from_attributes = True