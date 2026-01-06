from fastapi import APIRouter, Depends, status
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
from backend.schemas.seller import TokenResponse
from backend.service.seller_service import (
    create_seller_application,
    update_seller_profile,
    delete_seller_account,
    admin_approve_account,
    get_seller_from_token
)
from backend.models.seller import Seller
from backend.utils.auth import oauth2_scheme

from backend.core.error_handler import error_handler
router=APIRouter(prefix="/sellers",tags=["Seller "] )

@router.post("/apply", response_model=SellerResponse, status_code=201)
def apply_seller(data: SellerApplicationCreate, db: Session = Depends(get_db)):
    return create_seller_application(db,data)


@router.get("/me")
def get_current_user(token:str=Depends(oauth2_scheme)):
    return get_seller_from_token(token)