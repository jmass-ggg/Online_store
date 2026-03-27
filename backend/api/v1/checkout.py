from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.customer import Customer
from backend.models.order import PaymentMethod
from backend.schemas.order import (
    PlaceOrderRequest,
    PlaceOrderResponse,
    BuyNowRequest,
    BuyNowResponse,Checkout
)
from backend.service.order_service import place_order_service, buy_now_service
from backend.utils.jwt import get_current_customer
from backend.service.checkout_service import prepare_buy_now_checkout,cart_to_check_out
router = APIRouter(prefix="/checkout", tags=["Checkout for customer"])
from uuid import UUID


@router.post("/checkout")
def customer_checkout(
    payload: Checkout,
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
):
    checkout_result = prepare_buy_now_checkout(
        db=db,
        user_id=current_user.id,
        address_id=payload.address_id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
    )
    return checkout_result
 
 
@router.post("/checkout/{cart_id}")
def customer_cart_checkout(
    cart_id:UUID,
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
): 
    return cart_to_check_out(db, cart_id, user_id=current_user.id)