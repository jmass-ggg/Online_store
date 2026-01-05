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
    model_config = ConfigDict(from_attributes=True)

    id: int
    cart_id: int
    variant_id: int
    quantity: int
class CartCreate(BaseModel):
    buyer_id: int
    status: CartStauts = CartStauts.ACTIVE

class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buyer_id: int
    status: str  
    created_at: datetime
    updated_at: datetime
    items: List[CartItemOut] = []