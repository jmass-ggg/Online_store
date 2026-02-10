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

def get_or_create_active_cart(db:Session,buyer_id:int)->Cart:
    cart=db.query(Cart).options(selectinload(Cart.items)).filter(Cart.buyer_id ==  buyer_id,Cart.status == CartStauts.ACTIVE).first()
    if cart:
        return cart
    cart=Cart(buyer_id=buyer_id,status=CartStauts.ACTIVE.value)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    cart=db.query(Cart).options(selectinload(Cart.items)).filter(Cart.buyer_id ==  buyer_id,Cart.status == CartStauts.ACTIVE).first()
    return cart

def add_to_cart_by_customer(db:Session,buyer_id:int,variant_id:int,quantity:int)->Cart:
    cart=get_or_create_active_cart(db,buyer_id)
    variant=db.query(ProductVariant).filter(ProductVariant.id == variant_id,ProductVariant.is_active == True).one_or_none()
    if not variant:
        raise HTTPException(404, "Variant not found or inactive")
    if variant.stock_quantity < quantity:
        raise HTTPException(400, "Not enough stock")
    item=db.query(CartItem).filter(CartItem.cart_id == cart.id,
                                   CartItem.variant_id == variant_id).one_or_none()
    if item:
        item.quantity+=quantity
    else:
        db.add(CartItem(cart_id=cart.id,variant_id=variant_id,quantity=quantity,price=variant.price))
    db.commit()
    return get_or_create_active_cart(db,buyer_id)

def get_item_by_variant_id(db: Session, buyer_id: int, variant_id: int) -> CartItem:
    cart = get_or_create_active_cart(db, buyer_id)

    item = (
        db.query(CartItem)
        .filter(CartItem.cart_id == cart.id, CartItem.variant_id == variant_id)
        .first()
    )
    if not item:
        raise error_handler(404, "Cart item not found")
    return item


def uncart_the_product(db: Session, buyer_id: int, item_id: int) -> Cart:
    cart=get_or_create_active_cart(db,buyer_id)
    item=db.query(CartItem).filter(CartItem.id == item_id,CartItem.cart_id == cart.id).one_or_none()
    if not item:
        raise error_handler(404,"Cart item not found")
    db.delete(item)
    db.commit()

    return get_or_create_active_cart(db, buyer_id=buyer_id)

def decrease__item_quantity(item_id: int, payload: DecreaseQty, db: Session, buyer_id: int):
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

def clear_cart(db: Session, buyer_id: int) -> Cart:
    cart=get_or_create_active_cart(db,buyer_id)
    if not cart:
        raise error_handler(400,"cart not found")
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    db.commit()
    return get_or_create_active_cart(db, buyer_id)
