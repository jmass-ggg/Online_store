from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.utils.jwt import get_current_admin
from backend.schemas.seller import (
    SellerResponse,
    SellerVerificationUpdate,
)
from backend.service.seller_service import admin_approve_account

router = APIRouter(prefix="/admin", tags=["Admin Authentication"])


@router.put("/{seller_id}/approved", response_model=SellerResponse)
def review_seller(
    seller_id: int,
    seller_approved: SellerVerificationUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    return admin_approve_account(db, seller_id, seller_approved)
