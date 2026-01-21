from sqlalchemy.orm import Session
from backend.models.order_fullments import OrderFulfillment, FulfillmentStatus
from backend.models.order import Order
from backend.models.order_iteam import OrderItem
from sqlalchemy.orm import selectinload


def seller_accept_the_product(db: Session, seller_id: int):
    return (
        db.query(OrderFulfillment)
        .filter(OrderFulfillment.seller_id == seller_id)
        .options(
            selectinload(OrderFulfillment.order).selectinload(Order.shipping_address),
            selectinload(OrderFulfillment.order).selectinload(Order.user),
            selectinload(OrderFulfillment.items).selectinload(OrderItem.product),
            selectinload(OrderFulfillment.items).selectinload(OrderItem.variant),
        )
        .order_by(OrderFulfillment.created_at.desc())
        .all()
    )


def seller_carts(db: Session, seller_id: int):
    fulfillments = seller_accept_the_product(db, seller_id)
    result = []

    for f in fulfillments:
        order = f.order
        user = order.user
        addr = order.shipping_address

        if f.fulfillment_status == FulfillmentStatus.PENDING:
            action = "ACCEPT"
        elif f.fulfillment_status == FulfillmentStatus.ACCEPTED:
            action = "HANDOVER"
        else:
            action = None

        result.append({
            "order_id": f.order_id,
            "fulfillment_status": f.fulfillment_status.value,

            "customer": {
                "name": getattr(user, "username", None),
                "phone_number": getattr(user, "phone_number", None),
            },

            "shipping_address": {
                "region": addr.region if addr else None,
                "line1": addr.line1 if addr else None,
            },

            "items": [
                {
                    "product": item.product.product_name if item.product else None,
                    "variant": item.variant.color if item.variant else None,
                    "qty": item.quantity,
                    "price": float(item.unit_price),
                }
                for item in f.items
            ],

            "seller_subtotal": float(f.seller_subtotal),
            "action": action,
        })

    return result
