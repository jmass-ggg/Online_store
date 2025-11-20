from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.seller import (
    SellerApplicationCreate,
    SellerResponse,
    SellerReviewUpdate,
)
from backend.service.seller_service import (
    create_seller_application,
    seller_login,
    update_seller_profile
)
from backend.utils.jwt import get_current_user
from backend.core.error_handler import error_handler
router=APIRouter(prefix="/sellers",tags=["Seller Management"] )

@router.post("/apply", response_model=SellerResponse, status_code=201)
def apply_seller(data: SellerApplicationCreate, db: Session = Depends(get_db)):
    return create_seller_application(db,data)


# ---------------------------------------------------------
# 2) Approve/Reject Seller (Admin Only)
# ---------------------------------------------------------
@router.put("/{seller_id}/review", response_model=SellerResponse)
def review_seller(
    seller_id: int,
    review: SellerReviewUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # check_permission happens inside get_current_user or middleware
    try:
        seller = SellerService.approve(db, seller_id) if review.status == "APPROVED" else None
        # you can also add reject() method in service if needed
        return seller
    except DomainError as e:
        raise e.to_http()