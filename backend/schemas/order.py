from pydantic import BaseModel, Field
from typing import List
from enum import Enum
from decimal import Decimal
from backend.schemas.order_iteam import OrderItemCreate, OrderItemRead

class OrderStatus(str, Enum):
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class OrderBase(BaseModel):
    total_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    status: OrderStatus = Field(default=OrderStatus.PLACED)  # ✅ MATCH DB FIELD NAME

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderRead(OrderBase):
    id: int
    buyer_id: int
    items: List[OrderItemRead]

    class Config:
        from_attributes = True
