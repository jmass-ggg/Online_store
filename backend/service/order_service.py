from __future__ import annotations
from fastapi import HTTPException
from decimal import Decimal
from collections import defaultdict
from typing import Tuple
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from sqlalchemy import update
from sqlalchemy.orm import Session, selectinload,joinedload
from backend.service.checkout_service import prepare_buy_now_checkout
from backend.core.error_handler import error_handler
from backend.models.address import AddressCustomer
from backend.models.cart import Cart
from backend.models.cart_items import CartItem
from backend.models.product_variant import ProductVariant
from backend.models.order import Order
from backend.models.order_address import OrderAddress
from backend.models.order_item import OrderItem, OrderItemStatus
from backend.models.order_fullments import OrderFulfillment, FulfillmentStatus
from backend.models.seller import Seller
from backend.models.delivery_charge import DeliveryCharge
from backend.models.product import Product
from uuid import UUID



def _q2(x: Decimal) -> Decimal:
    return Decimal(x).quantize(Decimal("0.01"))

def _begin_tx(db:Session):
    return db.begin_nested() if db.in_transaction() else db.begin()

def buy_now_service(
    db: Session,
    *,
    user_id: UUID,
    address_id: UUID,
    variant_id: UUID,
    quantity: int,
    paymentmethod: PaymentMethod,
) -> Tuple[Order, Decimal, int]:
    try:
        if quantity <= 0:
            raise error_handler(400, "Quantity must be at least 1")
        tx=_begin_tx(db)
        with tx:
            data=prepare_buy_now_checkout(
                db=db,
                user_id=user_id,
                address_id=address_id,
                variant_id=variant_id,
                quantity=quantity
            )
            address=data["address"]
            variant=data["variant"]
            product=data["product"]
            seller_id=data["seller_id"]
            unit_price=data["unit_price"]
            items_subtotal=data["items_subtotal"]
            delivery_charge=data["delivery_charges"]
            grand_total=data["grand_total"]
            address = (
                db.query(AddressCustomer)
                .filter(AddressCustomer.id == address_id, AddressCustomer.customer_id == user_id)
                .first()
            )
            if not address:
                raise error_handler(404, "Address not found")

            variant = (
            db.query(ProductVariant)
            .options(joinedload(ProductVariant.product)
                     .joinedload(Product.seller)
                     .joinedload(Seller.delivery_charges))
            .filter(ProductVariant.id == variant_id)
            .first()
            )
            order = Order(
                customer_id=user_id,
                status="PLACED",
                total_price=grand_total,
                payment_method=paymentmethod,
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
                    variant_id=variant.id
                    ,quantity=quantity,
                    unit_price=unit_price,
                    line_total=items_subtotal,
                    item_status=OrderItemStatus.PENDING
                )
            )
            db.add(
                OrderFulfillment(
                    order_id=order.id,
                    seller_id=seller_id,
                    fulfillment_status=FulfillmentStatus.PENDING,
                    seller_subtotal=items_subtotal
                )
            )
            db.commit()
        return order, grand_total, 1
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Duplicated order"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=400,
                            detail="database error")
    
def buy_from_cart_service(
    db: Session,
    *,
    user_id: UUID,
    cart_id: UUID,
    paymentmethod: PaymentMethod,
) -> Tuple[Order, Decimal, int]:
    try:
        address = (
            db.query(AddressCustomer)
            .filter(AddressCustomer.customer_id == user_id)
            .first()
        )

        if not address:
            raise error_handler(404, "Address not found")

        cart = (
            db.query(Cart)
            .filter(Cart.id == cart_id, Cart.buyer_id == user_id)
            .with_for_update()
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.variant)
                .selectinload(ProductVariant.product)
                .selectinload(Product.seller)
                .selectinload(Seller.delivery)
            )
            .first()
        )

        if not cart:
            raise error_handler(404, "Cart not found")

        selected_items = [item for item in cart.items if item.selected]
        if not selected_items:
            raise error_handler(400, "cart items not found")

        seller_subtotals = defaultdict(lambda: Decimal("0.00"))
        subtotal = Decimal("0.00")
        seller_delivery_map = {}
        prepared_items = []

        for item in selected_items:
            variant = item.variant
            if not variant:
                raise error_handler(400, "Cart item variant not found")

            product = variant.product
            if not product:
                raise error_handler(400, "Product not found")

            seller = product.seller
            if not seller:
                raise error_handler(400, "Seller not found")

            if item.quantity <= 0:
                raise error_handler(400, f"Invalid quantity for item {item.id}")

            if not variant.is_active:
                raise error_handler(400, f"Variant {variant.id} is inactive")

            if variant.stock_quantity < item.quantity:
                raise error_handler(400, f"Insufficient stock for {product.product_name}")

            unit_price = Decimal(str(item.price))
            line_total = unit_price * item.quantity

            subtotal += line_total
            seller_subtotals[seller.id] += line_total

            if seller.id not in seller_delivery_map:
                seller_delivery_map[seller.id] = (
                    seller.delivery[0].delivery_charge
                    if seller.delivery else Decimal("0.00")
                )

            prepared_items.append({
                "cart_item": item,
                "variant": variant,
                "product": product,
                "seller": seller,
                "unit_price": unit_price,
                "line_total": line_total,
            })

        delivery_charge = sum(seller_delivery_map.values(), Decimal("0.00"))
        grand_total = subtotal + delivery_charge

        order = Order(
            buyer_id=user_id,
            status="PLACED",
            total_price=grand_total,
            payment_method=paymentmethod,
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
                country=address.country or "Nepal",
                latitude=address.latitude,
                longitude=address.longitude,
            )
        )

        for row in prepared_items:
            item = row["cart_item"]
            variant = row["variant"]
            product = row["product"]
            seller = row["seller"]
            unit_price = row["unit_price"]
            line_total = row["line_total"]

            db.add(
                OrderItem(
                    order_id=order.id,
                    seller_id=seller.id,
                    product_id=product.id,
                    variant_id=variant.id,
                    quantity=item.quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                    item_status=OrderItemStatus.PENDING,
                )
            )

            variant.stock_quantity -= item.quantity
            db.delete(item)

        for seller_id, seller_subtotal in seller_subtotals.items():
            db.add(
                OrderFulfillment(
                    order_id=order.id,
                    seller_id=seller_id,
                    fulfillment_status=FulfillmentStatus.PENDING,
                    seller_subtotal=seller_subtotal,
                )
            )

        db.commit()
        db.refresh(order)

        return order, grand_total, len(seller_subtotals)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicated order")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
                
            
            
            
            
            
            
def place_order_service(
    db: Session,
    *,
    user_id: UUID,
    address_id: UUID,
    paymentmethod: str,
) -> Tuple[Order, Decimal, int]:
  
    tx= _begin_tx(db)
    with tx:
        address = (
            db.query(AddressCustomer)
            .filter(AddressCustomer.customer_id == user_id, AddressCustomer.id == address_id)
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
        grand_total = _q2(items_subtotal )

        order = Order(
            buyer_id=user_id,
            status="PLACED",  
            total_price=grand_total,
            payment_method=paymentmethod,
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
    
    db.commit()

    return order, grand_total, len(seller_subtotals)

from backend.models.order import PaymentMethod

# def buy_now_service(
#     db: Session,
#     *,
#     user_id: UUID,
#     address_id: UUID,
#     variant_id: UUID,
#     quantity: int,
#     paymentmethod: PaymentMethod,
# ) -> Tuple[Order, Decimal, int]:
   
#     try:
#         if quantity <= 0:
#             raise error_handler(400, "Quantity must be at least 1")

#         tx = _begin_tx(db)
#         with tx:
#             address = (
#                 db.query(Address)
#                 .filter(Address.id == address_id, Address.customer_id == user_id)
#                 .first()
#             )
#             if not address:
#                 raise error_handler(404, "Address not found")

#             variant = (
#                 db.query(ProductVariant)
#                 .filter(ProductVariant.id == variant_id)
#                 .options(selectinload(ProductVariant.product))
#                 .with_for_update()
#                 .first()
#             )
#             if not variant:
#                 raise error_handler(404, "Variant not found")
#             if not getattr(variant, "is_active", True):
#                 raise error_handler(400, "Variant is inactive")
#             if variant.stock_quantity < quantity:
#                 raise error_handler(400, "Insufficient stock")

#             product = variant.product
#             if not product:
#                 raise error_handler(400, "Variant has no product")

#             seller_id = product.seller_id
#             unit_price = _q2(Decimal(str(getattr(variant, "price", None) or product.price)))
#             items_subtotal = _q2(unit_price * Decimal(quantity))
#             grand_total = _q2(items_subtotal + DELIVERY_CHARGE)

#             order = Order(
#                 buyer_id=user_id,
#                 status="PLACED",
#                 total_price=grand_total,
#                 payment_method=paymentmethod,
#             )
#             db.add(order)
#             db.flush()

#             db.add(
#                 OrderAddress(
#                     order_id=order.id,
#                     full_name=address.full_name,
#                     phone_number=address.phone_number,
#                     region=address.region,
#                     line1=address.line1,
#                     line2=address.line2,
#                     postal_code=address.postal_code,
#                     country=address.country or "Nepal",
#                     latitude=address.latitude,
#                     longitude=address.longitude,
#                 )
#             )

#             db.add(
#                 OrderItem(
#                     order_id=order.id,
#                     seller_id=seller_id,
#                     product_id=product.id,
#                     variant_id=variant.id,
#                     quantity=quantity,
#                     unit_price=unit_price,
#                     line_total=items_subtotal,  
#                     item_status=OrderItemStatus.PENDING,
#                 )
#             )

#             db.add(
#                 OrderFulfillment(
#                     order_id=order.id,
#                     seller_id=seller_id,
#                     fulfillment_status=FulfillmentStatus.PENDING,
#                     seller_subtotal=items_subtotal,  
#                 )
#             )

            
#             res = db.execute(
#                 update(ProductVariant)
#                 .where(ProductVariant.id == variant_id, ProductVariant.stock_quantity >= quantity)
#                 .values(stock_quantity=ProductVariant.stock_quantity - quantity)
#             )
#             if res.rowcount != 1:
#                 raise error_handler(400, "Insufficient stock")
#             db.commit()
#         return order, grand_total, 1
#     except IntegrityError:
#         db.rollback()
#         raise HTTPException(
#             status_code=400,
#             detail="Duplicated order"
#         )
#     except SQLAlchemyError:
#         db.rollback()
#         raise HTTPException(status_code=400,
#                             detail="database error")
