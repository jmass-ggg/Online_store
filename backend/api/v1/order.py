from __future__ import annotations

from fastapi import APIRouter, Depends,Form

from sqlalchemy.orm import Session
from backend.models.customer import Customer
from backend.database import get_db
from backend.schemas.order import PlaceOrderRequest, PlaceOrderResponse, UpdateFulfillmentStatusRequest,BuyNowRequest,BuyNowResponse
from backend.service.order_service import place_order_service,buy_now_service
from backend.utils.jwt import get_current_customer, get_current_seller
from backend.models.order import Order,PaymentMethod

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/order", response_model=PlaceOrderResponse, status_code=201)
def place_order_api(
    payload: PlaceOrderRequest,paymentmethod:PaymentMethod=Form(...),
    db: Session = Depends(get_db),
    current_user:Customer=Depends(get_current_customer),
):
    order, total_price, seller_count = place_order_service(
        db,
        user_id=current_user.id,
        address_id=payload.address_id,
        paymentmethod=paymentmethod
    )
    return PlaceOrderResponse(
        order_id=order.id,
        status=str(order.status),
        total_price=total_price,
        seller_count=seller_count,
    )


# @router.patch("/seller/fulfillments/{fulfillment_id}/status", status_code=200)
# def update_fulfillment_status_api(
#     fulfillment_id: int,
#     payload: UpdateFulfillmentStatusRequest,
#     db: Session = Depends(get_db),
#     current_seller:Customer=Depends(get_current_seller),
# ):
#     fulfillment = update_fulfillment_status_service(
#         db,
#         seller_id=current_seller.id,
#         fulfillment_id=fulfillment_id,
#         new_status=payload.status,
#         sync_item_status=True,
#     )

#     shipping = fulfillment.order.shipping_address
#     return {
#         "fulfillment_id": fulfillment.id,
#         "order_id": fulfillment.order_id,
#         "fulfillment_status": str(fulfillment.fulfillment_status),
#         "seller_subtotal": str(fulfillment.seller_subtotal),
#         "order_placed": fulfillment.order.order_placed,
#         "shipping": {
#             "full_name": shipping.full_name if shipping else None,
#             "phone_number": shipping.phone_number if shipping else None,
#             "region": shipping.region if shipping else None,
#             "line1": shipping.line1 if shipping else None,
#             "line2": shipping.line2 if shipping else None,
#             "postal_code": shipping.postal_code if shipping else None,
#             "country": shipping.country if shipping else None,
#             "latitude": shipping.latitude if shipping else None,
#             "longitude": shipping.longitude if shipping else None,
#         },
#         "items": [
#             {
#                 "id": i.id,
#                 "product_id": i.product_id,
#                 "variant_id": i.variant_id,
#                 "quantity": i.quantity,
#                 "unit_price": str(i.unit_price),
#                 "line_total": str(i.line_total),
#                 "item_status": str(i.item_status),
#             }
#             for i in (fulfillment.items or [])
#         ],
#     }

@router.post("/buy-now", response_model=BuyNowResponse, status_code=200)
def buy_now_api(
    payload: BuyNowRequest,paymentmethod:PaymentMethod=Form(...),
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
):
    order, total_price, seller_count = buy_now_service(
        db,
        user_id=current_user.id,
        address_id=payload.address_id,
        variant_id=payload.variant_id,
        quantity=payload.quantity,

    )
    return BuyNowResponse(
        order_id=order.id,
        status=str(order.status),
        total_price=total_price,
        seller_count=seller_count,
        paymentmethod=paymentmethod
    )