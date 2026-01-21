from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class CustomerOut(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None


class ShippingAddressOut(BaseModel):
    region: Optional[str] = None
    line1: Optional[str] = None


class DashboardItemOut(BaseModel):
    product: Optional[str] = None
    variant: Optional[str] = None
    qty: int
    price: float


class SellerDashboardOut(BaseModel):
    order_id: int
    fulfillment_status: str
    customer: CustomerOut
    shipping_address: ShippingAddressOut
    items: List[DashboardItemOut]
    seller_subtotal: float
    action: Optional[str] = None
