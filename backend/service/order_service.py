# backend/service/order_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from backend.models.order import Order
from backend.models.order_iteam import OrderItem
from backend.models.product import Product
from backend.schemas.order import OrderCreate, OrderRead
from backend.schemas.order_iteam import OrderItemCreate, OrderItemRead
from backend.models.customer import Customer

def order_the_product(
    order_in: OrderCreate,
    db: Session,
    current_user: case
) -> Order:
    """
    Create a new order for the current user with multiple items.
    Checks stock availability and calculates total price.
    """
    if not order_in.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total_price = 0.0
    order_items_list = []

    for item in order_in.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product {item.product_id} not found")

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for product '{product.product_name}'"
            )

        price = product.price * item.quantity
        total_price += price

        order_item = OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            price=product.price
        )
        order_items_list.append(order_item)

    new_order = Order(
        buyer_id=current_user.id,
        total_price=total_price,
        order_status="pending",
        order_at=datetime.utcnow(),
        items=order_items_list
    )

    for item in order_items_list:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock -= item.quantity

    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

def view_the_order(
    order_id: int,
    db: Session,
    current_user: User
) -> Order:
    """
    Retrieve a specific order for the current user.
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return order
