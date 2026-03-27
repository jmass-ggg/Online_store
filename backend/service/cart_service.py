from __future__ import annotations
from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from backend.schemas.cart import DecreaseQty
from backend.models.cart import Cart, CartStauts
from backend.models.cart_items import CartItem
from backend.models.ProductVariant import ProductVariant
from backend.core.error_handler import error_handler
from decimal import Decimal
from uuid import UUID
from backend.models.product import Product
from backend.models.seller import Seller
from backend.models.deliveryCharge import DeliveryCharge


def get_or_create_active_cart(db:Session,buyer_id:UUID)->Cart:
    cart=db.query(Cart).options(selectinload(Cart.items)).filter(Cart.buyer_id ==  buyer_id,Cart.status == CartStauts.ACTIVE).first()
    if cart:
        return cart
    cart=Cart(buyer_id=buyer_id,status=CartStauts.ACTIVE.value)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    cart=db.query(Cart).options(selectinload(Cart.items)).filter(Cart.buyer_id ==  buyer_id,Cart.status == CartStauts.ACTIVE).first()
    return cart

def add_to_cart_by_customer(
    db: Session,
    buyer_id: UUID,
    variant_id: UUID,
    quantity: int,
) -> Cart:
    cart = get_or_create_active_cart(db, buyer_id)

    variant = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.id == variant_id,
            ProductVariant.is_active.is_(True),
        )
        .one_or_none()
    )
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found or inactive")

    item = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart.id,
            CartItem.variant_id == variant_id,
        )
        .one_or_none()
    )

    new_quantity = quantity if item is None else item.quantity + quantity
    if variant.stock_quantity < new_quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    if item:
        item.quantity = new_quantity
        item.price = variant.price
    else:
        db.add(
            CartItem(
                cart_id=cart.id,
                variant_id=variant_id,
                quantity=quantity,
                price=variant.price,
                selected=False,
            )
        )

    db.commit()

    return (
        db.query(Cart)
        .options(selectinload(Cart.items))
        .filter(Cart.id == cart.id)
        .first()
    )

def to_cart_out(db:Session,cart: Cart) -> dict:
    loaded_cart=(
        db.query(Cart).filter(Cart.id == cart.id)
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

def select_cart_item(
    db: Session,
    buyer_id:UUID,
    cart_item_id,
    selected: bool,
) -> dict:
    cart_item = (
        db.query(CartItem)
        .join(Cart, Cart.id == CartItem.cart_id)
        .filter(
            CartItem.id == cart_item_id,
            Cart.buyer_id == buyer_id,
            Cart.status == "ACTIVE",
        )
        .options(
            selectinload(CartItem.variant)
            .selectinload(ProductVariant.product)
            .selectinload(Product.seller)
            
        )
        .with_for_update()
        .first()
    )

    if not cart_item:
        raise error_handler(404, "Cart item not found")

    cart_item.selected = selected
    db.commit()
    db.refresh(cart_item)
    cart=get_or_create_active_cart(db,buyer_id)
    return to_cart_out(db,cart)


def increase_decrease_cart_item(
    db: Session,
    buyer_id: UUID,
    cart_item_id: UUID,
    quantity: int
) -> dict:
    if quantity < 1:
        raise error_handler(400, "Quantity cannot be less than 1")

    cart_item = (
        db.query(CartItem)
        .join(Cart, Cart.id == CartItem.cart_id)
        .filter(
            CartItem.id == cart_item_id,
            Cart.buyer_id == buyer_id,
            Cart.status == "ACTIVE",
        )
        .options(
            selectinload(CartItem.variant)
            .selectinload(ProductVariant.product)
            .selectinload(Product.seller)
        )
        .with_for_update()
        .first()
    )

    if not cart_item:
        raise error_handler(404, "Cart item not found")

    if cart_item.variant.stock_quantity < quantity:
        raise error_handler(400, "Insufficient stock")

    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)

    cart = get_or_create_active_cart(db, buyer_id)
    return to_cart_out(db, cart)
    
    
    
# def get_item_by_variant_id(db: Session, buyer_id: UUID, variant_id: UUID) :
#     cart = get_or_create_active_cart(db, buyer_id)

#     item = (
#         db.query(CartItem)
#         .filter(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id)
#         .options(
#             selectinload(CartItem.variant)
#             .selectinload(ProductVariant.product)
            
#         ).first()
#     )
#     if not item:
#         raise error_handler(404, "Cart item not found")
#     return item

def get_item_by_variant_id(db:Session,cart: Cart) :

    loaded_cart=(
        db.query(Cart).filter(Cart.id == cart.id)
        .with_for_update()
        .options(
            selectinload(Cart.items)
            .selectinload(CartItem.variant)
            .selectinload(ProductVariant.product)
            
        ).first()
    )
    if not loaded_cart:
        raise error_handler(400, "Cart is empty")
    
    
    
    return {
        "cart_id": str(loaded_cart.id),
        "buyer_id": str(loaded_cart.buyer_id),
        "status": loaded_cart.status,
        "items": [
            {
                "cart_item_id": str(item.id),
                "quantity": item.quantity,
                "price": float(item.price),

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
                    "product_category": item.variant.product.product_category.value if item.variant.product.product_category else None,
                    "target_audience": item.variant.product.target_audience.value if item.variant.product.target_audience else None,
                    "description": item.variant.product.description,
                    "image_url": item.variant.product.image_url,
                    "status": item.variant.product.status.value if item.variant.product.status else None,
                } if item.variant and item.variant.product else None,
            }
            for item in loaded_cart.items
        ]
    }

def uncart_the_product(db: Session, buyer_id: UUID, item_id: UUID) -> Cart:
    cart=get_or_create_active_cart(db,buyer_id)
    item=db.query(CartItem).filter(CartItem.id == item_id,CartItem.cart_id == cart.id).one_or_none()
    if not item:
        raise error_handler(404,"Cart item not found")
    db.delete(item)
    db.commit()

    return get_or_create_active_cart(db, buyer_id=buyer_id)

def decrease__item_quantity(item_id: UUID, payload: DecreaseQty, db: Session, buyer_id: UUID):
    cart=get_or_create_active_cart(db,buyer_id)
    item=db.query(CartItem).filter(CartItem.id == item_id,
                                   CartItem.cart_id == cart.id).one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if item.quantity<1:
        raise HTTPException(400, "amount must be >= 1")
    if item.quantity>payload.amount:
        item.quantity-=payload.amount
    else:
        db.delete(item)
    return get_or_create_active_cart(db, buyer_id=buyer_id)





def cart_subtotal(cart: Cart) -> Decimal:
    total = Decimal("0.00")
    for item in cart.items:
        
        total += item.variant.price * item.quantity
    return total

def clear_cart(db: Session, buyer_id: UUID) -> Cart:
    cart=get_or_create_active_cart(db,buyer_id)
    if not cart:
        raise error_handler(400,"cart not found")
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    db.commit()
    return get_or_create_active_cart(db, buyer_id)
