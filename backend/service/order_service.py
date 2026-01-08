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
from backend.models.order_iteam import OrderItem  
from backend.models.order_fullments import OrderFulfillment  


_ALLOWED_STATUS = {"PENDING", "ACCEPTED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"}


def place_order_service(db: Session, *, user_id: int, address_id: int):
    tx = db.begin_nested() if db.in_transaction() else db.begin()

    with tx:
        address = (
            db.query(Address)
            .filter(Address.id == address_id, Address.customer_id == user_id)
            .first()
        )
        if not address:
            raise error_handler(404, "Address not found for this user")

        cart = (
            db.query(Cart)
            .filter(Cart.buyer_id == user_id, Cart.status == "ACTIVE")
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
            )
            .first()
        )
        if not cart or not cart.items:
            raise error_handler(400, "Cart is empty")

        variant_ids = [ci.variant_id for ci in cart.items]
        locked_variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.id.in_(variant_ids))
            .with_for_update()
            .options(selectinload(ProductVariant.product))
            .all()
        )
        variant_map = {v.id: v for v in locked_variants}

        order_total = Decimal("0.00")
        seller_subtotals: Dict[int, Decimal] = {}
        prepared_lines = []

        for ci in cart.items:
            v = variant_map.get(ci.variant_id)
            if not v or not v.is_active:
                raise error_handler(400, f"Variant {ci.variant_id} is unavailable")

            qty = int(ci.quantity)
            if v.stock_quantity < qty:
                raise error_handler(400, f"Insufficient stock for variant {v.id}")

            seller_id = v.product.seller_id
            unit_price = Decimal(str(v.price))
            line_total = (unit_price * Decimal(qty)).quantize(Decimal("0.01"))

            order_total += line_total
            seller_subtotals[seller_id] = seller_subtotals.get(seller_id, Decimal("0.00")) + line_total
            prepared_lines.append((seller_id, v.product_id, v.id, qty, unit_price, line_total))

        order_total = order_total.quantize(Decimal("0.01"))

        order = Order(buyer_id=user_id, status="PLACED", total_price=order_total)
        db.add(order)
        db.flush()

        db.add(OrderAddress(
            order_id=order.id,
            full_name=address.full_name,
            phone_number=address.phone_number,
            region=address.region,
            line1=address.line1,
            line2=address.line2,
            postal_code=address.postal_code,
            country=address.country or "Nepal",
            latitude=address.latitude,
            longitude=address.longitude,
        ))

        for (seller_id, product_id, variant_id, qty, unit_price, line_total) in prepared_lines:
            db.add(OrderItem(
                order_id=order.id,
                seller_id=seller_id,
                product_id=product_id,
                variant_id=variant_id,
                quantity=qty,
                unit_price=unit_price,
                line_total=line_total,
                item_status="PENDING",
            ))

        for seller_id, subtotal in seller_subtotals.items():
            db.add(OrderFulfillment(
                order_id=order.id,
                seller_id=seller_id,
                fulfillment_status="PENDING",
                seller_subtotal=subtotal.quantize(Decimal("0.01")),
            ))

        for ci in cart.items:
            variant_map[ci.variant_id].stock_quantity -= int(ci.quantity)

        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        cart.status = "CHECKED_OUT"

    return order, order_total, len(seller_subtotals)


def _set_status_timestamp(fulfillment, new_status: str) -> None:
    ts = datetime.utcnow()
    if new_status == "ACCEPTED" and fulfillment.accepted_at is None:
        fulfillment.accepted_at = ts
    elif new_status == "PACKED" and fulfillment.packed_at is None:
        fulfillment.packed_at = ts
    elif new_status == "SHIPPED" and fulfillment.shipped_at is None:
        fulfillment.shipped_at = ts
    elif new_status == "DELIVERED" and fulfillment.delivered_at is None:
        fulfillment.delivered_at = ts


def update_fulfillment_status_service(
    db: Session,
    *,
    seller_id: int,
    fulfillment_id: int,
    new_status: str,
    sync_item_status: bool = True,
):
    new_status = new_status.upper().strip()
    if new_status not in _ALLOWED_STATUS:
        raise error_handler(400, "Invalid status")

    with db.begin():
        fulfillment = (
            db.query(OrderFulfillment)
            .filter(OrderFulfillment.id == fulfillment_id, OrderFulfillment.seller_id == seller_id)
            .options(
                selectinload(OrderFulfillment.order).selectinload(Order.shipping_address),
                selectinload(OrderFulfillment.items),
            )
            .first()
        )
        if not fulfillment:
            raise error_handler(404, "Fulfillment not found")

        fulfillment.fulfillment_status = new_status
        _set_status_timestamp(fulfillment, new_status)

        if sync_item_status and fulfillment.items:
            for item in fulfillment.items:
                item.item_status = new_status

    return fulfillment

def buy_now_service(
    db: Session,
    *,
    user_id: int,
    address_id: int,
    variant_id: int,
    quantity: int,
):
    if quantity <= 0:
        raise error_handler(400, "Quantity must be at least 1")

    try:
        # 1) Address must belong to user
        address = (
            db.query(Address)
            .filter(Address.id == address_id, Address.customer_id == user_id)
            .first()
        )
        if not address:
            raise error_handler(404, "Address not found for this user")

        # 2) Load variant + lock row
        variant = (
            db.query(ProductVariant)
            .filter(ProductVariant.id == variant_id)
            .options(selectinload(ProductVariant.product))
            .with_for_update()
            .first()
        )
        if not variant:
            raise error_handler(404, "Variant not found")

        if not getattr(variant, "is_active", True):
            raise error_handler(400, "Variant is inactive")

        if variant.stock_quantity < quantity:
            raise error_handler(400, "Insufficient stock")

        product = variant.product
        if not product:
            raise error_handler(400, "Variant has no product")

        seller_id = product.seller_id
        unit_price = Decimal(str(variant.price))
        line_total = (unit_price * Decimal(quantity)).quantize(Decimal("0.01"))

        # 3) Create order rows
        order = Order(buyer_id=user_id, status="PLACED", total_price=line_total)
        db.add(order)
        db.flush()  # get order.id

        db.add(OrderAddress(
            order_id=order.id,
            full_name=address.full_name,
            phone_number=address.phone_number,
            region=address.region,
            line1=address.line1,
            line2=address.line2,
            postal_code=address.postal_code,
            country=address.country or "Nepal",
            latitude=address.latitude,
            longitude=address.longitude,
        ))

        db.add(OrderItem(
            order_id=order.id,
            seller_id=seller_id,
            product_id=product.id,
            variant_id=variant.id,
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
            item_status="PENDING",
        ))

        db.add(OrderFulfillment(
            order_id=order.id,
            seller_id=seller_id,
            fulfillment_status="PENDING",
            seller_subtotal=line_total,
        ))

        # 4) ✅ GUARANTEED stock decrement (DB-level)
        new_stock = db.execute(
            update(ProductVariant)
            .where(
                ProductVariant.id == variant_id,
                ProductVariant.stock_quantity >= quantity,
            )
            .values(stock_quantity=ProductVariant.stock_quantity - quantity)
            .returning(ProductVariant.stock_quantity)
        ).scalar_one_or_none()

        if new_stock is None:
            raise error_handler(400, "Insufficient stock")

        db.commit()  # ✅ commit everything (order + stock update)
        return order, line_total, 1

    except Exception:
        db.rollback()
        raise