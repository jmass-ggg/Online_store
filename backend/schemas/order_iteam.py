from pydantic import BaseModel,Field
from backend.schemas.product import Product_read
from decimal import Decimal

class OrderItemBase(BaseModel):
    product_id: int=Field(...,description="Id of the product being order")
    quantity: int=Field(...,description="Quantity of the order product")
    class Config:
        orm_mode = True
        from_attributes = True

class OrderItemCreate(OrderItemBase):
    pass   

class OrderItemRead(OrderItemBase):
    id: int 
    price: Decimal = Field(..., ge=0, description="Price per unit of the product")
    
    class Config:
        orm_mode = True
        from_attributes=True