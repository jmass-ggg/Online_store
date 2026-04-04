from fastapi import APIRouter, Depends, status,BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.database import get_db
from backend.schemas.seller import (
    SellerApplicationCreate,
    SellerResponse,
    SellerReviewUpdate,SellerVerificationUpdate
)
from backend.utils.jwt import create_refresh_token
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.utils.jwt import create_refresh_token,get_current_seller,get_current_admin
from backend.models.seller import Seller
from backend.utils.hashed import verify_password
from backend.schemas.seller import TokenResponse,SellerRegister,SellerRegisterRead
from backend.service.seller_service import (
    seller_register,verified_seller_email
)
from backend.utils.verifyied import verify_seller_or_not
from backend.service.seller_product_service import seller_carts
from backend.models.seller import Seller
from backend.utils.auth import oauth2_scheme
from backend.schemas.seller_dashboard import SellerDashboardOut
from backend.core.error_handler import error_handler
router=APIRouter(prefix="/seller",tags=["Seller"] )


@router.post("/apply",response_model=SellerRegisterRead)
def apply_seller(data:SellerRegister,background_tasks: BackgroundTasks,db:Session=Depends(get_db)):
    return seller_register(db,data,background_tasks)

@router.get("/verified-email")
def email_verified(token: str, db: Session = Depends(get_db)):
    return verified_seller_email(token,db)

@router.get("/me")
def get_seller(current_seller:Seller=Depends(get_current_seller)):
    return SellerRegisterRead.model_validate(current_seller)

# @router.post("/apply", response_model=SellerResponse, status_code=201)
# def apply_seller(data: SellerApplicationCreate, db: Session = Depends(get_db)):
#     return create_seller_application(db,data)


# @router.get("/me")
# def get_current_user(token:str=Depends(oauth2_scheme)):
    # return get_seller_from_token(token)

