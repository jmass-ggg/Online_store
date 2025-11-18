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
   SellerUpdate
)
from backend.utils.jwt import create_token, verify_token
from backend.utils.hashed import hashed_password, verify_password
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler


def seller_application(
    db:Session,
) -> SellerResponse:
    """Allow a customer to apply for a seller account."""

    existing_application = db.query(Seller).filter(Seller.id == current_user.id).first()
    if existing_application:
        raise error_handler(status.HTTP_302_FOUND, "Seller application already exists")

    new_application = Seller(
        

        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        kyc_document_type=application_data.kyc_document_type,
        kyc_document_number=application_data.kyc_document_number,
        kyc_document_url=application_data.kyc_document_url,
        business_license_number=application_data.business_license_number,
        bank_account_number=application_data.bank_account_number,
        bank_account_name=application_data.bank_account_name,
        bank_name=application_data.bank_name,
        bank_branch=application_data.bank_branch
    )

    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return SellerResponse.from_orm(new_application)