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
DELIVERY_CHARGE=100

def place_order_service(db:Session,user_id:int,address_id:int):
    tx=db.begin_nested() if db.in_transaction() else db.begin()
    with tx:
        address=db.query(Address).filter(Address.customer_id == user_id,Address.id == address_id).first()
        if not address:
            raise error_handler(400,"USer not found")
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
            raise error_handler(400,"Car is empty")
        variant_qty=defaultdict(int)
        for ci in cart.items:
            q=int(ci.quantity)
            if q<=0:
                raise error_handler(400,"Cart is empty")
            variant_qty[ci.variant_id]+=q
        variant_ids=sorted(variant_qty.keys())
        variants=db.query(ProductVariant)\
            .filter(ProductVariant.id.in_(variant_ids))\
            .with_for_update()\
            .options(selectinload(ProductVariant.product))\
                .all()
        variant_map={v.id:v for v in variants}
        for vid in variant_ids:
            v=variant_map.get(vid)
            if not v:
                raise error_handler(400, f"Variant {vid} not found")
            if not v.is_active:
                raise error_handler(400, f"Variant {vid} is unavailable")
            if v.stock_quantity < variant_qty[vid]:
                raise error_handler(400, f"Insufficient stock for variant {vid}")
        
        order_total = Decimal("0.00")
        seller_subtotals = defaultdict(lambda: Decimal("0.00"))
        order_items = []

        for ci in cart.items:
            v = variant_map[ci.variant_id]

            qty = int(ci.quantity)
            unit_price = Decimal(str(v.price)).quantize(Decimal("0.01"))
            line_total = (unit_price * Decimal(qty)).quantize(Decimal("0.01"))

            seller_id = v.product.seller_id
            order_total += line_total
            seller_subtotals[seller_id] += line_total

            order_items.append(
                OrderItem(
                    seller_id=seller_id,
                    product_id=v.product_id,
                    variant_id=v.id,
                    quantity=qty,
                    unit_price=unit_price,     
                    line_total=line_total,
                    item_status="PENDING",
                )
            )

        order_total = order_total.quantize(Decimal("0.01"))
        grand_total=(order_total+DELIVERY_CHARGE).quantize(Decimal("0.01"))
        order = Order(
            buyer_id=user_id,
            status="PLACED",
            total_price=grand_total,
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
                seller_subtotal=subtotal.quantize(Decimal("0.01")),
            )
            for seller_id, subtotal in seller_subtotals.items()
        ]
        db.add_all(fulfillments)


        for vid in variant_ids:
            qty = variant_qty[vid]
            result = db.execute(
                update(ProductVariant)
                .where(
                    ProductVariant.id == vid,
                    ProductVariant.stock_quantity >= qty,
                )
                .values(stock_quantity=ProductVariant.stock_quantity - qty)
            )
            if result.rowcount != 1:
                raise error_handler(400, f"Insufficient stock for variant {vid}")
        
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        cart.status = "CHECKED_OUT"
        db.commit()
    return order, order_total, len(seller_subtotals)

def buy_now_service(
    db: Session,
   
    user_id: int,
    address_id: int,
    variant_id: int,
    quantity: int,
):
    if quantity<=0:
        raise error_handler(400,"Quantity must be at least 1 ")
    try:
        address=db.query(Address).filter(Address.id == address_id,Address.customer_id == user_id).first()
        if not address:
            raise error_handler(400,"Address not found for this user")
        variant=(db.query(ProductVariant).
                 filter(ProductVariant.id == variant_id).
                 options(selectinload(ProductVariant.product)).
                 with_for_update().first())
        if not variant:
            raise error_handler(404, "Variant not found")

        if not getattr(variant, "is_active", True):
            raise error_handler(400, "Variant is inactive")

        if variant.stock_quantity < quantity:
            raise error_handler(400, "Insufficient stock")
        product=variant.product
        if not product:
            raise error_handler(400,"Product has not variant")
        seller_id=product.seller_id
        unit_price=Decimal(str(product.price))
        line_price=(quantity*Decimal(unit_price)).quantize(Decimal("0.01"))
        grand_total=(line_price+DELIVERY_CHARGE).quantize(Decimal("0.01"))
        order=Order(buyer_id=user_id,
                    status="PLACED",
                    total_price=grand_total)
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
        db.add(OrderItem(
            order_id=order.id,
            seller_id=seller_id,
            product_id=product.id,
            variant_id=variant.id,
            quantity=quantity,
            unit_price=unit_price,
            line_total=grand_total,
            item_status=OrderItemStatus.PENDING
        ))
        db.add(OrderFulfillment(
            order_id=order.id,
            seller_id=seller_id,
            fulfillment_status=FulfillmentStatus.PENDING,
            seller_subtotal=grand_total
        ))
        new_stock = db.execute(
            update(ProductVariant)
            .where(
                ProductVariant.id == variant_id,
                ProductVariant.stock_quantity >= quantity,
            )
            .values(stock_quantity=ProductVariant.stock_quantity - quantity)
            .returning(ProductVariant.stock_quantity)
        ).scalar_one_or_none()
        if not new_stock:
            raise error_handler(404, "Fulfillment not found")
        db.commit()  
        return order, line_price, 1

    except Exception: 
        db.rollback()
        raise
        
# def seller_accept_order(db:Session,user_id:int,address_id:int,order_id:int):




# def _set_status_timestamp(fulfillment, new_status: str) -> None:
#     ts = datetime.utcnow()
#     if new_status == "ACCEPTED" and fulfillment.accepted_at is None:
#         fulfillment.accepted_at = ts
#     elif new_status == "PACKED" and fulfillment.packed_at is None:
#         fulfillment.packed_at = ts
#     elif new_status == "SHIPPED" and fulfillment.shipped_at is None:
#         fulfillment.shipped_at = ts
#     elif new_status == "DELIVERED" and fulfillment.delivered_at is None:
#         fulfillment.delivered_at = ts


# def update_fulfillment_status_service(
#     db: Session,
#     *,
#     seller_id: int,
#     fulfillment_id: int,
#     new_status: str,
#     sync_item_status: bool = True,
# ):
#     new_status = new_status.upper().strip()
#     if new_status not in _ALLOWED_STATUS:
#         raise error_handler(400, "Invalid status")

#     with db.begin():
#         fulfillment = (
#             db.query(OrderFulfillment)
#             .filter(OrderFulfillment.id == fulfillment_id, OrderFulfillment.seller_id == seller_id)
#             .options(
#                 selectinload(OrderFulfillment.order).selectinload(Order.shipping_address),
#                 selectinload(OrderFulfillment.items),
#             )
#             .first()
#         )
#         if not fulfillment:
#             raise error_handler(404, "Fulfillment not found")

#         fulfillment.fulfillment_status = new_status
#         _set_status_timestamp(fulfillment, new_status)

#         if sync_item_status and fulfillment.items:
#             for item in fulfillment.items:
#                 item.item_status = new_status

#       return fulfillment