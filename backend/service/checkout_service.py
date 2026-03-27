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



def cart_to_check_out(
    db:Session,
    cart_id:UUID,
    *,
    user_id: UUID,
    
):
    address=db.query(Address).filter(
        Address.customer_id == user_id
    ).first()
    if not address:
        raise error_handler(400, "Address not found")
    loaded_cart=(
        db.query(Cart).filter(Cart.id == cart_id)
        .with_for_update()
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.variant)
            .selectinload(ProductVariant.product)
            
        ).first()
    )
    if not loaded_cart:
        raise error_handler(400, "Cart is empty")
    select_items=[item for item in loaded_cart.items if item.selected]
    subtotal=sum(
        (item.price* item.quantity  for item in select_items),Decimal("0.00")
    )
    seller_delivery_map={}
    for item in select_items:
        if not item.variant or not item.variant.product or not item.variant.product.seller:
            continue
        seller = item.variant.product.seller
        seller_id = str(seller.id)
        if seller_id not in seller_delivery_map:
            charge=(
                seller.delivery[0].delivery_charge
                if seller.delivery else Decimal("0.00")
            )
            seller_delivery_map[seller_id]=charge
    delivery_charge=sum(seller_delivery_map.values(),Decimal("0.00"))
    total=subtotal+delivery_charge
        
        
    return {
        "cart_id": str(loaded_cart.id),
        "buyer_id": str(loaded_cart.buyer_id),
        "status": loaded_cart.status,

        "selected_count": len(select_items),
        "subtotal": float(subtotal),
        "delivery_charge": float(delivery_charge),
        "total": float(total),
        "address":address,
        "delivery_breakdown": [
            {
                "seller_id": seller_id,
                "delivery_charge": float(charge),
            }
            for seller_id, charge in seller_delivery_map.items()
        ],


        "items": [
            {
                "cart_item_id": str(item.id),
                "quantity": item.quantity,
                "price": float(item.price),
                "line_total": float(item.price * item.quantity),
                "selected": item.selected,

                "product_variant": {
                    "variant_id": str(item.variant.id),
                    "sku": item.variant.sku,
                    "color": item.variant.color,
                    "size": item.variant.size,
                    "price": float(item.variant.price),
                    "stock_quantity": item.variant.stock_quantity,
                    "is_active": item.variant.is_active,
                } if item.variant else None,

                "product": {
                    "product_id": str(item.variant.product.id),
                    "product_name": item.variant.product.product_name,
                    "url_slug": item.variant.product.url_slug,
                    "product_category": item.variant.product.product_category.value
                        if item.variant.product.product_category else None,
                    "target_audience": item.variant.product.target_audience.value
                        if item.variant.product.target_audience else None,
                    "description": item.variant.product.description,
                    "image_url": item.variant.product.image_url,
                    "status": item.variant.product.status.value
                        if item.variant.product.status else None,
                    "seller_id": str(item.variant.product.seller.id)
                        if item.variant.product.seller else None,
                } if item.variant and item.variant.product else None,
            }
            for item in loaded_cart.items
        ]
    }
    

# def checkout(
#     db: Session,
#     user_id: UUID,
#     address_id: UUID,
#     variant_id: UUID,
#     quantity: int,
# ):
#     with _begin_tx(db):
#         data = prepare_buy_now_checkout(
#             db=db,
#             user_id=user_id,
#             address_id=address_id,
#             variant_id=variant_id,
#             quantity=quantity,
#         )

#         address = data["address"]
#         variant = data["variant"]

#         return {
#             "address": {
#                 "id": address.id,
#                 "full_name": address.full_name,
#                 "phone_number": address.phone_number,
#                 "region": address.region,
#                 "line1": address.line1,
#                 "line2": address.line2,
#                 "country": address.country,
#             },
#             "product": {
#                 "product_variant_id": variant.id,
#                 "product_name": variant.product.product_name,
#                 "price": str(data["unit_price"]),
#                 "quantity": quantity,
#                 "subtotal": str(data["items_subtotal"]),
#             },
#             "delivery_charge": str(data["delivery_charge"]),
#             "grand_total": str(data["grand_total"]),
#         }