from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List

from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update
from backend.core.error_handler import error_handler
from backend.models.cart_items import CartItem
from backend.models.cart import Cart
from backend.models.address import Address
from backend.models.ProductVariant import ProductVariant 
from backend.models.order import Order
from backend.models.order_address import OrderAddress
from backend.models.order_iteam import OrderItem,OrderItemStatus
from backend.models.order_fullments import OrderFulfillment  ,FulfillmentStatus  
from collections import defaultdict

_ALLOWED_STATUS = {"PENDING", "ACCEPTED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"}

def seller_accept_the_product(db:Session,user_id:int,address_id:int):
    order=db.query(Order).filter(Order.buyer_id == user_id).options(selectinload(Order.items),selectinload(Order.fulfillments)).all()
    if not order:
        raise error_handler(400,"No order")
    