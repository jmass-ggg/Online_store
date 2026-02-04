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
    BuyNowResponse,
)
from backend.service.order_service import place_order_service, buy_now_service
from backend.utils.jwt import get_current_customer

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/order", response_model=PlaceOrderResponse, status_code=201)
def place_order_api(
    payload: PlaceOrderRequest,
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
):
   
    order, total_price, seller_count = place_order_service(
        db,
        user_id=current_user.id,
        address_id=payload.address_id,
        paymentmethod=str(payload.payment_method),
    )

    payment_redirect_url = None
    if payload.payment_method == PaymentMethod.ESEWA:
       
        payment_redirect_url = f"/payments/esewa/initiate?order_id={order.id}"

    return PlaceOrderResponse(
        order_id=order.id,
        status=str(order.status),
        total_price=total_price,
        seller_count=seller_count,
        payment_method=str(order.payment_Method),
        payment_redirect_url=payment_redirect_url,
    )


@router.post("/buy-now", response_model=BuyNowResponse, status_code=200)
def buy_now_api(
    payload: BuyNowRequest,
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
):
    order, total_price, seller_count = buy_now_service(
        db,
        user_id=current_user.id,
        address_id=payload.address_id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
        paymentmethod=str(payload.payment_method),
    )

    payment_redirect_url = None
    if payload.payment_method == PaymentMethod.ESEWA:
        payment_redirect_url = f"/payments/esewa/initiate?order_id={order.id}"

    return BuyNowResponse(
        order_id=order.id,
        status=str(order.status),
        total_price=total_price,
        seller_count=seller_count,
        paymentmethod=str(payload.payment_method),
        payment_redirect_url=payment_redirect_url,  
    )