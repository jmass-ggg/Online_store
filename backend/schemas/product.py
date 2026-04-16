from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from backend.models.product import ProductCategory, ProductStatus, TargetAudience


class ProductCreate(BaseModel):
    product_name: str = Field(..., min_length=2, max_length=255)
    target_audience: TargetAudience
    product_category: ProductCategory
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    status: Optional[ProductStatus] = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: str
    url_slug: str
    target_audience: TargetAudience
    product_category: ProductCategory
    description: Optional[str] = None
    status: ProductStatus
    seller_id: UUID
    created_at: datetime
    updated_at: datetime


class ProductListRead(ProductRead):
    model_config = ConfigDict(from_attributes=True)

    default_variant_id: Optional[UUID] = None
    default_price: Optional[Decimal] = None


class ProductVariantCreate(BaseModel):
    color: str | None = None
    size: str | None = None
    price: Decimal = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)


class ProductVariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    sku: str
    color: str | None = None
    size: str | None = None
    price: Decimal
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


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

    color: Optional[str] = None
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)


class AllProduct(ProductRead):
    model_config = ConfigDict(from_attributes=True)
    
    variants: List[ProductVariantRead] = []
    images: List[ProductImageRead] = []


class ProductSuggestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: str
    url_slug: str
    image_url: str | None = None