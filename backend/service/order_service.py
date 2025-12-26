# backend/service/order_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from backend.core.error_handler import error_handler
from backend.models.order import Order
from backend.models.order_iteam import OrderItem
from backend.models.product import Product
from backend.schemas.order import OrderCreate, OrderRead
from backend.schemas.order_iteam import OrderItemCreate, OrderItemRead
from backend.models.customer import Customer
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends
from backend.database import get_db
from typing import List
from typing import List
from datetime import datetime
from decimal import Decimal

from typing import List
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.order import Order, OrderStatus as DBOrderStatus
from backend.models.order_iteam import OrderItem
from backend.models.product import Product
from backend.models.customer import Customer
from backend.schemas.order import OrderCreate


def order_the_product(order_in: OrderCreate, current_user: Customer, db: Session) -> Order:
    if not order_in.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    try:
        # 1) bulk fetch + lock
        product_ids: List[int] = [i.product_id for i in order_in.items]

        products = (
            db.query(Product)
            .filter(Product.id.in_(product_ids))
            .with_for_update()
            .all()
        )
        product_map = {p.id: p for p in products}

        total_price = Decimal("0.00")
        order_items: List[OrderItem] = []

        # 2) validate + update stock
        for item in order_in.items:
            product = product_map.get(item.product_id)
            if product is None:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

            if product.stock < item.quantity:
                raise HTTPException(status_code=400, detail=f"Not enough stock for '{product.product_name}'")

            product.stock -= item.quantity

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    price=product.price,
                )
            )
            total_price += product.price * item.quantity

        # 3) create order
        new_order = Order(
            buyer_id=current_user.id,
            total_price=total_price,
            status=DBOrderStatus.PLACED,
            order_placed=datetime.utcnow(),
            delivered_at=None,   # if nullable in model
            items=order_items,
        )

        db.add(new_order)
        db.commit()            # ✅ commit here
        db.refresh(new_order)
        return new_order

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError as e:
        db.rollback()
        print("SQLAlchemyError:", repr(e))
        raise HTTPException(status_code=500, detail="Order creation failed")

def view_the_order(
    order_id: int,
    db: Session,
    current_user: Customer
) -> Order:
    """
    Retrieve a specific order for the current user.
    """
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.buyer_id == current_user.id
        ).one_or_none()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        return OrderRead.from_orm(order)
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order view failed")


def view_all_order(db:Session,current_user:Customer):
    try:
        order=db.query(Order).all()
        return order
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order view failed")