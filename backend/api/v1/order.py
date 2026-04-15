from fastapi import APIRouter, Depends, Request, Body
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.customer import CustomerProfile
from backend.models.order import PaymentMethod
from backend.models.address import AddressCustomer
from backend.schemas.order import (
    PlaceOrderRequest,
    PlaceOrderResponse,
    BuyNowRequest,
    BuyNowResponse,BuyCartRequest                                                                                                       
)
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.service.order_service import place_order_service, buy_now_service,buy_from_cart_service
from backend.utils.jwt import get_current_customer
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/orders", tags=["Orders"])
limiter=Limiter(key_func=get_remote_address)


@router.post("/order", response_model=PlaceOrderResponse, status_code=201)

@limiter.limit("10/minute")
def place_order_api(
    request: Request,
    payload: PlaceOrderRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: CustomerProfile = Depends(get_current_customer),
):
    order, total_price, seller_count = place_order_service(
        db,
        user_id=current_user.id,
        address_id=payload.address_id,
        paymentmethod=payload.payment_method.value,
    )

    payment_redirect_url = None
    if payload.payment_method == PaymentMethod.ESEWA:
        payment_redirect_url = f"/payments/esewa/initiate?order_id={order.id}"

    return PlaceOrderResponse(
        order_id=order.id,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        total_price=total_price,
        seller_count=seller_count,
        payment_method=order.payment_method.value if hasattr(order.payment_method, "value") else str(order.payment_method),
        payment_redirect_url=payment_redirect_url,
    )

@router.post("/buy-now", response_model=BuyNowResponse, status_code=200)
@limiter.limit("10/minute")
def buy_now_api(
    request: Request,
    payload: BuyNowRequest,
    db: Session = Depends(get_db),
    current_user: CustomerProfile = Depends(get_current_customer),
):
    order, total_price, seller_count = buy_now_service(
        db,
        user_id=current_user.id,
        address_id=payload.address_id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,
        paymentmethod=payload.payment_method.value,
    )

    payment_redirect_url = None
    if payload.payment_method == PaymentMethod.ESEWA:
        payment_redirect_url = f"/payments/esewa/initiate?order_id={order.id}"

    return BuyNowResponse(
        order_id=order.id,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        total_price=total_price,
        seller_count=seller_count,
        payment_method=order.payment_method.value if hasattr(order.payment_method, "value") else str(order.payment_method),
        payment_redirect_url=payment_redirect_url,
    )
    
    
@router.post("/buy_product", response_model=BuyNowResponse, status_code=200)
@limiter.limit("10/minute")
def buy_product_from_cart_to_payment(
    request: Request,
    payload: BuyCartRequest,
    db: Session = Depends(get_db),
    current_user: CustomerProfile = Depends(get_current_customer),
):
    order, total_price, seller_count = buy_from_cart_service(
        db=db,
        user_id=current_user.id,
        cart_id=payload.cart_id,
        paymentmethod=payload.payment_method,
    )

    payment_redirect_url = None
    if payload.payment_method == PaymentMethod.ESEWA:
        payment_redirect_url = f"/payments/esewa/initiate?order_id={order.id}"

    return BuyNowResponse(
        order_id=order.id,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        total_price=total_price,
        seller_count=seller_count,
        payment_method=order.payment_method,
        payment_redirect_url=payment_redirect_url,
    )