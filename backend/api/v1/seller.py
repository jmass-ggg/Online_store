from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.seller import Seller
from backend.schemas.seller import (
    SellerBusinessAddressCreate,
    SellerBusinessAddressRead,
    SellerDetail,
    SellerPersonalInformationRead,
    SellerRegisterRead,
    SellerRegisterRequest,
    SellerRegisterResponse,
)
from backend.service.seller_service import (
    get_seller_detail,
    register_seller,
    seller_business_address_create,
    seller_business_address_read,
    seller_information_fill,
    seller_information_read,
    verify_seller_email,
)
from backend.utils.jwt import get_current_seller
from backend.utils.verifyied import verify_email_seller_or_not

router = APIRouter(prefix="/seller", tags=["Seller"])


@router.post(
    "/apply",
    response_model=SellerRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_seller(
    payload: SellerRegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SellerRegisterResponse:
    return register_seller(db, payload, background_tasks)


@router.get("/verify-email", status_code=status.HTTP_200_OK)
def email_verified(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    return verify_seller_email(token, db)





@router.post(
    "/seller-information",
    response_model=SellerPersonalInformationRead,
    status_code=status.HTTP_201_CREATED,
)
def full_seller_information(
    legal_name: str = Form(...),
    pan_number: str = Form(...),
    account_name: str = Form(...),
    account_number: str = Form(...),
    bank_name: str = Form(...),
    branch_name: str = Form(...),
    business_document_photo: UploadFile = File(...),
    cheque_photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_email_seller_or_not),
):
    return seller_information_fill(
        db=db,
        current_seller=current_seller,
        legal_name=legal_name,
        pan_number=pan_number,
        account_name=account_name,
        account_number=account_number,
        bank_name=bank_name,
        branch_name=branch_name,
        business_document_photo=business_document_photo,
        cheque_photo=cheque_photo,
    )


@router.get(
    "/your-information",
    response_model=SellerPersonalInformationRead,
    status_code=status.HTTP_200_OK,
)
def get_your_information(
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return seller_information_read(db, current_seller)


@router.post(
    "/business-address",
    response_model=SellerBusinessAddressRead,
    status_code=status.HTTP_201_CREATED,
)
def create_business_address(
    data: SellerBusinessAddressCreate,
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_email_seller_or_not),
):
    return seller_business_address_create(db, current_seller, data)


@router.get(
    "/business-address",
    response_model=SellerBusinessAddressRead,
    status_code=status.HTTP_200_OK,
)
def get_business_address(
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return seller_business_address_read(db, current_seller)


@router.get(
    "/me",
    response_model=SellerRegisterRead,
    status_code=status.HTTP_200_OK,
)
def get_seller(
    current_seller: Seller = Depends(get_current_seller),
):
    return SellerRegisterRead(
        seller_id=current_seller.id,
        user_id=current_seller.user_id,
        username=current_seller.user.username,
        email=current_seller.user.email,
        account_type=current_seller.account_type,
        status=current_seller.status,
        is_verified=current_seller.is_verified,
        is_email_verified=current_seller.user.is_email_verified,
        role_name=current_seller.role_name,
    )
    
    
@router.get(
    "/{seller_id}/detail",
    response_model=SellerDetail,
    status_code=status.HTTP_200_OK,
)
def seller_detail(
    seller_id: UUID,
    db: Session = Depends(get_db),
):
    return get_seller_detail(db, seller_id)