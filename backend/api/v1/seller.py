from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.database import get_db
from backend.schemas.seller import (
    SellerApplicationCreate,
    SellerResponse,
    SellerReviewUpdate,
)
from backend.utils.jwt import create_token,create_refresh_token
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.utils.jwt import create_token, create_refresh_token
from backend.models.seller import Seller
from backend.utils.hashed import verify_password
from backend.schemas.customer import LoginResponse
from backend.schemas.seller import TokenResponse
from backend.service.seller_service import (
    create_seller_application,
    seller_login,
    update_seller_profile,
    delete_seller_account
)
from backend.models.seller import Seller
from backend.utils.auth import oauth2_scheme

from backend.core.error_handler import error_handler
router=APIRouter(prefix="/sellers",tags=["Seller Management"] )

@router.post("/apply", response_model=SellerResponse, status_code=201)
def apply_seller(data: SellerApplicationCreate, db: Session = Depends(get_db)):
    return create_seller_application(db,data)

@router.post("/login", response_model=LoginResponse)
def seller_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    seller = db.query(Seller).filter(Seller.email == form.username).first()
    if not seller:
        raise error_handler(404, "Seller not found")

    if not verify_password(form.password, seller.hashed_password):
        raise error_handler(401, "Invalid password")

    access = create_token({"email": seller.email})
    refresh = create_refresh_token(db, seller)
    return LoginResponse(access_token=access, refresh_token=refresh)



# ---------------------------------------------------------
# 2) Approve/Reject Seller (Admin Only)
# ---------------------------------------------------------
# @router.put("/{seller_id}/review", response_model=SellerResponse)
# def review_seller(
#     seller_id: int,
#     review: SellerReviewUpdate,
#     db: Session = Depends(get_db),
#     current_user=Depends(get_current_user),
# ):
#     # check_permission happens inside get_current_user or middleware
#     try:
#         seller = SellerService.approve(db, seller_id) if review.status == "APPROVED" else None
#         # you can also add reject() method in service if needed
#         return seller
#     except DomainError as e:
#         raise e.to_http()

# @router.delete("/admin/{seller_id}/delete",status_code=status.HTTP_200_OK)
# def delete_seller_account(seller_id:int,
#                           db:Session=Depends(get_db),
#                           current_user=Depends(get_current_user)):
    


# @router.delete("/delete/by_own",status_code=status.HTTP_200_OK)
# def delete_own_seller_account(db:Session=Depends(get_db),
#                           current_user=Depends(get)):
#     return delete_own_seller_account(db,current_user)