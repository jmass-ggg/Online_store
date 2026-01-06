from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.cart import CartOut, CartItemAdd,DecreaseQty
from backend.utils.jwt import get_current_customer
from backend.models.customer import Customer
from backend.service.cart_service import (
    add_to_cart_by_customer,
    get_or_create_active_cart,
    uncart_the_product,decrease__item_quantity,clear_cart
)

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("/me", response_model=CartOut)
def get_my_cart(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return get_or_create_active_cart(db, buyer_id=current_customer.id)


@router.post("/items", response_model=CartOut)
def add_to_cart(
    payload: CartItemAdd,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return add_to_cart_by_customer(
        db=db,
        buyer_id=current_customer.id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
    )

@router.patch("/items/{item_id}/decrease", response_model=CartOut)
def item_quantity_delete(item_id: int,
    payload: DecreaseQty,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)):
    return decrease__item_quantity(item_id,payload,db,current_customer.id)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    return uncart_the_product(db=db, buyer_id=current_customer.id, item_id=item_id)

@router.delete("/all-item/delete")
def delete_all_item(db:Session=Depends(get_db),current_user:Customer=Depends(get_current_customer)):
    return clear_cart(db,current_user.id)