from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field, ConfigDict
from backend.models.cart import CartStatus
from uuid import UUID

class CartItemAdd(BaseModel):
    variant_id: UUID
    quantity: int = Field(default=1, ge=1)


class DecreaseQty(BaseModel):
    amount: int = Field(default=1, ge=1)


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cart_id: UUID
    variant_id: UUID
    quantity: int
    price: Decimal 


class CartOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    buyer_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    subtotal: Decimal
    items: List[CartItemOut] = Field(default_factory=list)


class ProductOnlyOut(BaseModel):
    id: UUID
    product_name: str
    url_slug: str
    image_url: str | None = None

class ProductVariantOnlyOut(BaseModel):
    id: UUID
    sku: str
    color: str | None = None
    size: str | None = None
    price: Decimal
    stock_quantity: int

class CartItemProductOut(BaseModel):
    quantity: int
    product_variant: ProductVariantOnlyOut
    product: ProductOnlyOut
class CartProductsOut(BaseModel):
    cart_id: UUID
    buyer_id: UUID
    status: str
    items: list[CartItemProductOut] = Field(default_factory=list)
class ProductMiniOut(BaseModel):
    id: UUID
    product_name: str
    image_url: str | None = None

class ProductVariantMiniOut(BaseModel):
    id: UUID
    sku: str
    color: str | None = None
    size: str | None = None
    price: Decimal
    stock_quantity: int
    
class CartItemSelectIn(BaseModel):
    selected: bool
    
class SelectedCartItemOut(BaseModel):
    cart_item_id: UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    selected: bool
    product: ProductMiniOut
    product_variant: ProductVariantMiniOut

class CartSelectionOut(BaseModel):
    selected_count: int
    subtotal: Decimal
    delivery_free: Decimal
    total: Decimal
    items: list[SelectedCartItemOut]