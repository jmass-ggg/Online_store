from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db
from backend.models.seller import Seller
from backend.models.role import Roles
from backend.schemas.seller import (
   SellerApplicationCreate,
   SellerReviewUpdate,
   SellerResponse,
   SellerUpdate,SellerVerificationUpdate
)
from backend.schemas.customer import LoginResponse
from backend.schemas.seller import TokenResponse
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.utils.jwt import create_token, verify_token
from backend.utils.hashed import  verify_password
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler
from backend.utils.jwt import create_token, verify_token,create_refresh_token,get_current_seller


def verify_seller_or_not(seller:Seller=Depends(get_current_seller)):
    if seller.is_verified == "REJECTED" or seller.status != False:
        raise error_handler(status.HTTP_401_UNAUTHORIZED,"Not authorized")
    return seller