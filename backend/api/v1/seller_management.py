from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.schemas.seller import (
    SellerApplicationCreate,
    SellerResponse,
    SellerReviewUpdate,SellerVerificationUpdate
)
from backend.models.order import Order,PaymentMethod
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.utils.jwt import create_refresh_token,get_current_seller,get_current_admin
from backend.models.seller import Seller
from backend.utils.hashed import verify_password
from backend.schemas.seller_dashboard import (CustomerOut,ShippingAddressOut,DashboardItemOut,SellerDashboardOut,OrderActionResponse)
from backend.service.seller_product_service import (
   seller_accept_the_product,
   seller_carts,
   accept_order,
   handover_the_product

)

from backend.utils.verifyied import verify_seller_or_not
from backend.service.seller_product_service import seller_carts
from backend.models.seller import Seller
from backend.utils.auth import oauth2_scheme
from backend.schemas.seller_dashboard import SellerDashboardOut
from backend.core.error_handler import error_handler 

router=APIRouter(prefix="/seller_managements",tags=["seller"])

@router.get("/Accept",response_model=list[SellerDashboardOut])
def all_user_cart_seen_by_seller(db:Session=Depends(get_db)
                                 ,current_user:Seller=Depends(get_current_seller)):
    return seller_carts(db,current_user.id)

@router.post("/orders/{order_id}/accept",response_model=OrderActionResponse)
def accept_seller_order(customer_id:int,order_id:int,db:Session=Depends(get_db),current_user:Seller=Depends(get_current_seller)):
    return accept_order(db,customer_id,current_user.id,order_id)

@router.post("/orders/{order_id}/handover",response_model=OrderActionResponse)
def accept_seller_order(customer_id:int,order_id:int,db:Session=Depends(get_db),current_user:Seller=Depends(get_current_seller)):
    return handover_the_product(db,customer_id,current_user.id,order_id)