from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.schemas.order import OrderCreate, OrderRead
from backend.schemas.order_iteam import OrderItemRead, OrderItemCreate
from backend.utils.jwt import get_current_customer
from backend.models.customer import Customer
from backend.service.order_service import order_the_product, view_the_order

router=APIRouter(prefix="/order",tags=["Order"])

@router.post("/", response_model=OrderRead)
def place_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: Customer = Depends(get_current_customer),
):
    
    return order_the_product(order_in, db, current_user)

@router.get("/{order_id}/get_oder",response_model=OrderRead)
def get_order(order_id:int,
              db:Session=Depends(get_db),
              current_user:Customer=Depends(get_current_customer)):
    return view_the_order(order_id,db,current_user)
