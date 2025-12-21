from pydantic import BaseModel,Field
from typing import List
from datetime import datetime
from enum import Enum
from backend.schemas.order_iteam import OrderItemCreate, OrderItemRead
from decimal import Decimal
class OrderStatus(str,Enum):
    PLACED = "PLACED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    
class OrderBase(BaseModel):
    total_price: Decimal = Field(default=Decimal("0.0"), ge=0, description="Total price of the order")
    order_status: str = Field(default=OrderStatus.PLACED, description="Current status of the order")
    class Config:
        orm_mode = True
        from_attributes = True
    
class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., description="List of items in the order")

class OrderRead(OrderBase):
    id: int = Field(..., description="Unique ID of the order")
    buyer_id: int = Field(..., description="ID of the buyer")
    items: List[OrderItemRead] = Field(..., description="List of items in the order")  

    class Config:
        orm_mode = True
        from_attributes = True
