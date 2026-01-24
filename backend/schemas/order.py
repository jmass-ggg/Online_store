from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PlaceOrderRequest(BaseModel):
    address_id: int = Field(..., gt=0)
    payment_method: str

class PlaceOrderResponse(BaseModel):
    order_id: int
    status: str
    total_price: Decimal
    seller_count: int
    payment_method: str
    payment_redirect_url: Optional[str] = None


class SellerFulfillmentItem(BaseModel):
    id: int
    product_id: int
    variant_id: int
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    item_status: str


class SellerOrderAddressOut(BaseModel):
    full_name: str
    phone_number: str
    region: str
    line1: str
    line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SellerFulfillmentOut(BaseModel):
    fulfillment_id: int
    order_id: int
    fulfillment_status: str
    seller_subtotal: Decimal
    order_placed: datetime
    shipping: SellerOrderAddressOut
    items: List[SellerFulfillmentItem]


class UpdateFulfillmentStatusRequest(BaseModel):
    status: str

class BuyNowRequest(BaseModel):
    address_id: int = Field(..., gt=0)
    variant_id: int = Field(..., gt=0)
    quantity: int = Field(1, ge=1)

class BuyNowResponse(BaseModel):
    order_id: int
    status: str
    total_price: Decimal
    seller_count: int