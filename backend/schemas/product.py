from pydantic import BaseModel, ConfigDict, Field, constr
from decimal import Decimal
from backend.models.product import ProductCategory, ProductStatus
from typing import List

class ProductCreate(BaseModel):
    product_name: constr(min_length=5, max_length=50)  # 15 is too short in real apps
    url_slug: str = Field(..., min_length=3, max_length=80)
    product_category: ProductCategory
    description: str | None = None


class ProductUpdate(BaseModel):
    product_name: str | None = Field(None, min_length=5, max_length=50)
    description: str | None = None
    status: ProductStatus | None = None


class ProductRead(ProductCreate):

    id: int
    status: ProductStatus
    seller_id: int
    class Config:
        orm_mode=True
        from_attributes=True


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