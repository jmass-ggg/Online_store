from __future__ import annotations
from fastapi import HTTPException
from decimal import Decimal
from collections import defaultdict
from typing import Tuple
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from sqlalchemy import update
from sqlalchemy.orm import Session, selectinload,joinedload

from backend.core.error_handler import error_handler
from backend.models.address import Address
from backend.models.cart import Cart
from backend.models.cart_items import CartItem
from backend.models.ProductVariant import ProductVariant
from backend.models.order import Order
from backend.models.order_address import OrderAddress
from backend.models.order_iteam import OrderItem, OrderItemStatus
from backend.models.order_fullments import OrderFulfillment, FulfillmentStatus
from backend.models.seller import Seller
from backend.models.deliveryCharge import DeliveryCharge
from backend.models.product import Product
from uuid import UUID


def _begin_tx(db:Session):
    return db.begin_nested() if db.in_transaction() else db.begin()

def prepare_buy_now_checkout(
    db: Session,
    *,
    user_id: UUID,
    address_id: UUID,
    variant_id: UUID,
    quantity: int,
):
    address = (
        db.query(Address)
        .filter(
            Address.customer_id == user_id,
            Address.id == address_id,
        )
        .first()
    )
    if not address:
        raise error_handler(400, "Address not found")

    variant = (
        db.query(ProductVariant)
        .filter(ProductVariant.id == variant_id)
        .with_for_update()
        .first()
    )
    if not variant:
        raise error_handler(400, "Variant not found")

   
    product = (
        db.query(Product)
        .options(
            joinedload(Product.seller).joinedload(Seller.delivery)
        )
        .filter(Product.id == variant.product_id)
        .first()
    )
    if not product:
        raise error_handler(400, "Product not found")

    if not variant.is_active:
        raise error_handler(400, "Variant is inactive")

    if variant.stock_quantity < quantity:
        raise error_handler(400, "Insufficient stock")

    if product.status.value != "active":
        raise error_handler(400, "Product is inactive")

    unit_price = Decimal(variant.price)
    items_subtotal = unit_price * quantity

    delivery_charge = Decimal("0.00")
    if product.seller and product.seller.delivery:
        delivery_charge = Decimal(product.seller.delivery[0].delivery_charge)

    grand_total = items_subtotal + delivery_charge

    return {
        "address": address,
        "variant": variant,
        "product": product,
        "seller_id": product.seller_id,
        "unit_price": unit_price,
        "items_subtotal": items_subtotal,
        "delivery_charge": delivery_charge,
        "grand_total": grand_total,
    }
    
def checkout(
    db: Session,
    user_id: UUID,
    address_id: UUID,
    variant_id: UUID,
    quantity: int,
):
    with _begin_tx(db):
        data = prepare_buy_now_checkout(
            db=db,
            user_id=user_id,
            address_id=address_id,
            variant_id=variant_id,
            quantity=quantity,
        )

        address = data["address"]
        variant = data["variant"]

        return {
            "address": {
                "id": address.id,
                "full_name": address.full_name,
                "phone_number": address.phone_number,
                "region": address.region,
                "line1": address.line1,
                "line2": address.line2,
                "country": address.country,
            },
            "product": {
                "product_variant_id": variant.id,
                "product_name": variant.product.product_name,
                "price": str(data["unit_price"]),
                "quantity": quantity,
                "subtotal": str(data["items_subtotal"]),
            },
            "delivery_charge": str(data["delivery_charge"]),
            "grand_total": str(data["grand_total"]),
        }