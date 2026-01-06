from pydantic import BaseModel, Field, constr
from decimal import Decimal
from backend.models.product import ProductCategory, ProductStatus,TargetAudience
from typing import List, Optional
from datetime import datetime

class ProductCreate(BaseModel):
    product_name: constr(min_length=5, max_length=50)
    url_slug: str = Field(..., min_length=3, max_length=80)
    target_audience:TargetAudience
    product_category: ProductCategory
    description: Optional[str] = None

class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=5, max_length=50)
    description: Optional[str] = None
    status: Optional[ProductStatus] = None

class ProductRead(ProductCreate):
    id: int
    status: ProductStatus
    seller_id: int
    image_url: str | None = None   

    class Config:
        orm_mode = True
        from_attributes = True

class ProductVariantCreate(BaseModel):
    color: str | None = None
    size: str | None = None
    price: Decimal = Field(..., gt=0)          
    stock_quantity: int = Field(..., ge=0)     


class ProductVariantRead(ProductVariantCreate):

    id: int
    product_id: int
    sku:str
    class Config:
        orm_mode=True
        from_attributes=True

class AllProduct(ProductRead):
    variants: List[ProductVariantRead] = []

class ProductSuggestion(BaseModel):
    id: int
    product_name: str
    url_slug: str
    image_url: str | None = None

    class Config:
        orm_mode = True
        from_attributes=True

class ProductImageBase(BaseModel):
    color:str | None = None
    is_primary: bool = False
    sort_order: int = Field(0, ge=0)
    

class ProductImageRead(ProductImageBase):
    id: int
    product_id: int
    image_url: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class ProductImageUpdate(BaseModel):
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    color:str | None = None

    class Config:
        orm_mode = True
        from_attributes = True