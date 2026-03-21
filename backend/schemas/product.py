from pydantic import BaseModel, Field, constr, ConfigDict
from decimal import Decimal
from backend.models.product import ProductCategory, ProductStatus, TargetAudience
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class ProductCreate(BaseModel):
    product_name: constr(min_length=5, max_length=50)
    url_slug: str = Field(..., min_length=3, max_length=80)
    target_audience: TargetAudience
    product_category: ProductCategory
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=5, max_length=50)
    description: Optional[str] = None
    status: Optional[ProductStatus] = None


class ProductRead(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: ProductStatus
    seller_id: UUID
    image_url: str | None = None


class ProductListRead(ProductRead):
    model_config = ConfigDict(from_attributes=True)

    default_variant_id: Optional[UUID] = None
    default_price: Optional[Decimal] = None


class ProductVariantCreate(BaseModel):
    color: str | None = None
    size: str | None = None
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)


class ProductVariantRead(ProductVariantCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    sku: str


class AllProduct(ProductRead):
    model_config = ConfigDict(from_attributes=True)

    variants: List[ProductVariantRead] = []


class ProductSuggestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: str
    url_slug: str
    image_url: str | None = None


class ProductImageBase(BaseModel):
    color: str | None = None
    is_primary: bool = False
    sort_order: int = Field(0, ge=0)


class ProductImageRead(ProductImageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    image_url: str
    created_at: datetime


class ProductImageUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_primary: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    color: str | None = None