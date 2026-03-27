from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, constr,ConfigDict
from uuid import UUID
from pydantic import BaseModel, Field
from backend.models.order import PaymentMethod

class PlaceOrderRequest(BaseModel):
    address_id: UUID 
    payment_method: PaymentMethod

class PlaceOrderResponse(BaseModel):
    order_id: UUID
    status: str
    total_price: Decimal
    seller_count: int
    payment_method: PaymentMethod
    payment_redirect_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class SellerFulfillmentItem(BaseModel):
    id: UUID
    product_id: UUID
    variant_id: UUID
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
    fulfillment_id: UUID
    order_id: UUID
    fulfillment_status: str
    seller_subtotal: Decimal
    order_placed: datetime
    shipping: SellerOrderAddressOut
    items: List[SellerFulfillmentItem]


class UpdateFulfillmentStatusRequest(BaseModel):
    status: str

class Checkout(BaseModel):
    address_id:UUID
    variant_id:UUID
    quantity:int

class BuyNowRequest(BaseModel):
    address_id: UUID
    variant_id: UUID
    quantity: int = Field(..., gt=0)
    payment_method: PaymentMethod
    
class BuyCartRequest(BaseModel):
    cart_id: UUID
    payment_method: PaymentMethod
    
class BuyNowResponse(BaseModel):
    order_id: UUID
    status: str
    total_price: Decimal
    seller_count: int
    payment_method: PaymentMethod
    payment_redirect_url: Optional[str] = None