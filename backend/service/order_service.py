from __future__ import annotations

from decimal import Decimal
from collections import defaultdict
from typing import Tuple

from sqlalchemy import update
from sqlalchemy.orm import Session, selectinload

from backend.core.error_handler import error_handler
from backend.models.address import Address
from backend.models.cart import Cart
from backend.models.cart_items import CartItem
from backend.models.ProductVariant import ProductVariant
from backend.models.order import Order
from backend.models.order_address import OrderAddress
from backend.models.order_iteam import OrderItem, OrderItemStatus
from backend.models.order_fullments import OrderFulfillment, FulfillmentStatus

DELIVERY_CHARGE = Decimal("100.00")


def _q2(x: Decimal) -> Decimal:
    return Decimal(x).quantize(Decimal("0.01"))

def _begin_tx(db:Session):
    return db.begin_nested() if db.in_transaction() else db.begin()


def place_order_service(
    db: Session,
    *,
    user_id: int,
    address_id: int,
    paymentmethod: str,
) -> Tuple[Order, Decimal, int]:
  
    tx= _begin_tx(db)
    with tx:
        address = (
            db.query(Address)
            .filter(Address.customer_id == user_id, Address.id == address_id)
            .first()
        )
        if not address:
            raise error_handler(404, "Address not found")

        cart = (
            db.query(Cart)
            .filter(Cart.buyer_id == user_id, Cart.status == "ACTIVE")
            .with_for_update()
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
            )
            .first()
        )
        if not cart or not cart.items:
            raise error_handler(400, "Cart is empty")

        variant_qty = defaultdict(int)
        for ci in cart.items:
            qty = int(ci.quantity)
            if qty <= 0:
                raise error_handler(400, "Invalid cart quantity")
            variant_qty[ci.variant_id] += qty

        variant_ids = sorted(variant_qty.keys())
        variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.id.in_(variant_ids))
            .with_for_update()
            .options(selectinload(ProductVariant.product))
            .all()
        )
        variant_map = {v.id: v for v in variants}

        for vid in variant_ids:
            v = variant_map.get(vid)
            if not v:
                raise error_handler(404, f"Variant {vid} not found")
            if not getattr(v, "is_active", True):
                raise error_handler(400, f"Variant {vid} is unavailable")
            if v.stock_quantity < variant_qty[vid]:
                raise error_handler(400, f"Insufficient stock for variant {vid}")

        items_subtotal = Decimal("0.00")
        seller_subtotals = defaultdict(lambda: Decimal("0.00"))
        order_items = []

        for ci in cart.items:
            v = variant_map[ci.variant_id]
            qty = int(ci.quantity)

            unit_price = _q2(Decimal(str(v.price)))
            line_total = _q2(unit_price * Decimal(qty))

            seller_id = v.product.seller_id
            items_subtotal += line_total
            seller_subtotals[seller_id] += line_total

            order_items.append(
                OrderItem(
                    seller_id=seller_id,
                    product_id=v.product_id,
                    variant_id=v.id,
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=line_total,
                    item_status=OrderItemStatus.PENDING,
                )
            )

        items_subtotal = _q2(items_subtotal)
        grand_total = _q2(items_subtotal + DELIVERY_CHARGE)

        order = Order(
            buyer_id=user_id,
            status="PLACED",  
            total_price=grand_total,
            payment_Method=paymentmethod,
        )
        db.add(order)
        db.flush()

        db.add(
            OrderAddress(
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
            )
        )

        for oi in order_items:
            oi.order_id = order.id
        db.add_all(order_items)

        fulfillments = [
            OrderFulfillment(
                order_id=order.id,
                seller_id=seller_id,
                fulfillment_status=FulfillmentStatus.PENDING,
                seller_subtotal=_q2(subtotal),
            )
            for seller_id, subtotal in seller_subtotals.items()
        ]
        db.add_all(fulfillments)
        
        for vid in variant_ids:
            qty = variant_qty[vid]
            res = db.execute(
                update(ProductVariant)
                .where(ProductVariant.id == vid, ProductVariant.stock_quantity >= qty)
                .values(stock_quantity=ProductVariant.stock_quantity - qty)
            )
            if res.rowcount != 1:
                raise error_handler(400, f"Insufficient stock for variant {vid}")

        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        cart.status = "CHECKED_OUT"
        

    return order, items_subtotal, len(seller_subtotals)


def buy_now_service(
    db: Session,
    *,
    user_id: int,
    address_id: int,
    variant_id: int,
    quantity: int,
    paymentmethod: str,
) -> Tuple[Order, Decimal, int]:
    """
    Creates single-item order with delivery charge.
    Returns: (order, items_subtotal, seller_count)
    """
    if quantity <= 0:
        raise error_handler(400, "Quantity must be at least 1")

    tx = _begin_tx(db)
    with tx:
        address = (
            db.query(Address)
            .filter(Address.id == address_id, Address.customer_id == user_id)
            .first()
        )
        if not address:
            raise error_handler(404, "Address not found")

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
        unit_price = _q2(Decimal(str(getattr(variant, "price", None) or product.price)))
        items_subtotal = _q2(unit_price * Decimal(quantity))
        grand_total = _q2(items_subtotal + DELIVERY_CHARGE)

        order = Order(
            buyer_id=user_id,
            status="PLACED",
            total_price=grand_total,
            payment_Method=paymentmethod,
        )
        db.add(order)
        db.flush()

        db.add(
            OrderAddress(
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
            )
        )

        db.add(
            OrderItem(
                order_id=order.id,
                seller_id=seller_id,
                product_id=product.id,
                variant_id=variant.id,
                quantity=quantity,
                unit_price=unit_price,
                line_total=items_subtotal,  
                item_status=OrderItemStatus.PENDING,
            )
        )

        db.add(
            OrderFulfillment(
                order_id=order.id,
                seller_id=seller_id,
                fulfillment_status=FulfillmentStatus.PENDING,
                seller_subtotal=items_subtotal,  
            )
        )

        
        res = db.execute(
            update(ProductVariant)
            .where(ProductVariant.id == variant_id, ProductVariant.stock_quantity >= quantity)
            .values(stock_quantity=ProductVariant.stock_quantity - quantity)
        )
        if res.rowcount != 1:
            raise error_handler(400, "Insufficient stock")
        
    return order, items_subtotal, 1