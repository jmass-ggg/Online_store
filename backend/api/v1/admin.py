from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.utils.jwt import get_current_admin
from backend.schemas.seller import (
    SellerRegisterRead,SellerDetail,
    SellerVerificationUpdate,
)
from backend.service.seller_service import admin_approve_account,get_seller_detail
from uuid import UUID
router = APIRouter(prefix="/admin", tags=["Admin Authentication"])


@router.get("Seller",response_model=SellerDetail)
def seller_details(seller_id: UUID,
    
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
    ):
    return get_seller_detail(db,seller_id)

@router.put("/{seller_id}/approved", response_model=SellerDetail)
def review_seller(
    seller_id: UUID,
    seller_approved: SellerVerificationUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    return admin_approve_account(db, seller_id, seller_approved)
