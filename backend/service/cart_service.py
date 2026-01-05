from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from backend.schemas.cart import DecreaseQty
from backend.models.cart import Cart, CartStauts
from backend.models.cart_items import CartItem
from backend.models.ProductVariant import ProductVariant


def get_or_create_active_cart(db: Session, buyer_id: int) -> Cart:
    stmt = (
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.buyer_id == buyer_id, Cart.status == CartStauts.ACTIVE.value)
    )

    cart = db.execute(stmt).scalars().first()
    if cart:
        return cart

    cart = Cart(buyer_id=buyer_id, status=CartStauts.ACTIVE.value)
    db.add(cart)
    db.commit()
    db.refresh(cart)

    cart = db.execute(stmt).scalars().first()
    return cart


def add_to_cart_by_customer(db: Session, buyer_id: int, variant_id: int, quantity: int) -> Cart:
    cart = get_or_create_active_cart(db, buyer_id=buyer_id)

    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.is_active == True
    ).first()

    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found or inactive")

    if variant.stock_quantity < quantity:
        raise HTTPException(status_code=400, detail="Not enough stock")

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.variant_id == variant_id
    ).first()

    if item:
        item.quantity += quantity
    else:
        db.add(CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity))

    db.commit()

    return get_or_create_active_cart(db, buyer_id=buyer_id)


def uncart_the_product(db: Session, buyer_id: int, item_id: int) -> Cart:
    cart = get_or_create_active_cart(db, buyer_id=buyer_id)

    item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.cart_id == cart.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    db.delete(item)
    db.commit()

    return get_or_create_active_cart(db, buyer_id=buyer_id)

def decrease__item_quantity(item_id: int,
    payload: DecreaseQty,
    db: Session ,
    buyer_id:int ):
    cart = get_or_create_active_cart(db, buyer_id=buyer_id)
    item=db.query(CartItem).filter(CartItem.id ==item_id,CartItem.cart_id == cart.id ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if not item.quantity >payload.amount:
        item.quantity-=payload.amount
    else:
        db.delete(item)
    db.commit()
    return get_or_create_active_cart(db, buyer_id=buyer_id)
