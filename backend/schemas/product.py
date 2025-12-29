from pydantic import BaseModel,constr,Field,validator
from datetime import datetime
from typing import Optional
from backend.schemas.seller import SellerBase
from decimal import Decimal
from backend.models.product import ProductCategory,ProductStatus

class ProductCreate(BaseModel):
    product_name: str
    url_slug: str
    product_category: ProductCategory
    description: str | None = None


class ProductUpdate(BaseModel):
    product_name: str | None = None
    description: str | None = None
    status: ProductStatus | None = None


class ProductRead(ProductCreate):
    id: int
    status: ProductStatus
    seller_id: int

    class Config:
        from_attributes = True
        orm_mode=True

class ProductVariantCreate(BaseModel):
    color: str | None = None
    size: str | None = None
    price: Decimal
    stock_quantity: int