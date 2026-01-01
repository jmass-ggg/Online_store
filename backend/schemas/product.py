from pydantic import BaseModel, Field, constr
from decimal import Decimal
from backend.models.product import ProductCategory, ProductStatus
from typing import List, Optional

class ProductCreate(BaseModel):
    product_name: constr(min_length=5, max_length=50)
    url_slug: str = Field(..., min_length=3, max_length=80)
    product_category: ProductCategory
    description: Optional[str] = None

class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=5, max_length=50)
    description: Optional[str] = None
    status: Optional[ProductStatus] = None

class ProductRead(BaseModel):
    id: int
    product_name: str
    url_slug: str
    product_category: ProductCategory
    description: Optional[str] = None

    image_url: Optional[str] = None  
    status: ProductStatus
    seller_id: int

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
    class Config:
        orm_mode=True
        from_attributes=True

class AllProduct(ProductRead):
    ProductVariants:List[ProductVariantRead]

class ProductSuggestion(BaseModel):
    id: int
    product_name: str
    url_slug: str
    image_url: str | None = None

    class Config:
        orm_mode = True