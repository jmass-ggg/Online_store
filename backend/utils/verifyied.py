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
from backend.schemas.seller import TokenResponse
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.utils.hashed import  verify_password
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler
from backend.utils.jwt import get_current_seller


def verify_seller_or_not(
    seller: Seller = Depends(get_current_seller)
):
    if seller.status == "REJECTED":
        raise error_handler(status.HTTP_403_FORBIDDEN, "Seller rejected")

    if not seller.is_verified:
        raise error_handler(status.HTTP_403_FORBIDDEN, "Seller not verified")

    return seller