from pydantic import BaseModel,constr,Field
from datetime import datetime
from typing import Optional
from backend.schemas.seller import SellerBase

class ProductBase(BaseModel):
    product_name: constr(min_length=3, max_length=100) = Field(..., description="Name of the product")
    product_category: Optional[str] = Field(None, description="Category of the product")
    class Config:
        orm_mode = True
        from_attributes = True
    

class Product_create(ProductBase):
    stock: int = Field(..., ge=0, description="Available stock")
    price: float = Field(..., ge=0.0, description="Product price")
    description: Optional[str] = Field(None, description="Product description")

    class Config:
        orm_mode = True
        from_attributes = True
    
    
class Product_read(ProductBase):
    id:int
    stock: int
    price: float
    description: Optional[str] = None
    image_url:str
    
    class Config:
        orm_mode = True
        from_attributes = True


class Product_update(BaseModel):
    product_name: Optional[constr(min_length=3, max_length=100)] = Field(None, description="Updated product name")
    product_category: Optional[str] = Field(None, description="Updated product category")
    stock: Optional[int] = Field(None, ge=0, description="Updated stock")
    price: Optional[float] = Field(None, ge=0.0, description="Updated price")
    description: Optional[str] = Field(None, description="Updated description")

    class Config:
        orm_mode = True
        from_attributes = True