from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.cart import CartOut, CartItemAdd, DecreaseQty,CartItemOut
from backend.utils.jwt import get_current_customer
from backend.models.customer import Customer
from backend.models.cart import Cart
from backend.models.cart_items import CartItem
from backend.service.cart_service import (
    add_to_cart_by_customer,
    get_or_create_active_cart,
    uncart_the_product,
    decrease__item_quantity,
    clear_cart,
    cart_subtotal,
    get_item_by_variant_id
)

router = APIRouter(prefix="/cart", tags=["Cart"])


def to_cart_out(cart: Cart) -> dict:
    return {
        "id": cart.id,
        "buyer_id": cart.buyer_id,
        "status": cart.status,
        "created_at": cart.created_at,
        "updated_at": cart.updated_at,
        "items": cart.items,
        "subtotal": cart_subtotal(cart),
    }


@router.get("/me", response_model=CartOut)
def get_my_cart(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = get_or_create_active_cart(db, buyer_id=current_customer.id)
    return to_cart_out(cart)

@router.get("/items/by-variant/{variant_id}", response_model=CartItemOut)
def get_the_item(
    variant_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    item = get_item_by_variant_id(db, current_customer.id, variant_id)
    return item

    

@router.post("/items", response_model=CartOut)
def add_to_cart(
    payload: CartItemAdd,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = add_to_cart_by_customer(
        db=db,
        buyer_id=current_customer.id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
    )
    return to_cart_out(cart)


@router.patch("/items/{item_id}/decrease", response_model=CartOut)
def item_quantity_delete(
    item_id: int,
    payload: DecreaseQty,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = decrease__item_quantity(item_id, payload, db, current_customer.id)
    return to_cart_out(cart)



@router.delete("/items/{item_id}", response_model=CartOut)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    cart = uncart_the_product(db=db, buyer_id=current_customer.id, item_id=item_id)
    return to_cart_out(cart)


@router.delete("/all-item/delete", response_model=CartOut)
def delete_all_item(
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
):
    cart = clear_cart(db, current_user.id)
    return to_cart_out(cart)
