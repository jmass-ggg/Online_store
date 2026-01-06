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
from backend.utils.jwt import  verify_token
from backend.utils.hashed import  verify_password
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler
from backend.utils.jwt import  verify_token,create_refresh_token
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import IntegrityError
from typing import Dict
from fastapi import status
def create_seller_application(db: Session, data: SellerApplicationCreate) -> SellerResponse:
    """Seller submits application. Default status = PENDING."""

    seller = Seller(
        username=data.username,
        email=data.email,
        phone_number=data.phone_number,
        hashed_password=hashed_pwd(data.password),

        business_name=data.business_name,
        business_type=data.business_type,
        business_address=data.business_address,

        kyc_document_type=data.kyc_document_type,
        kyc_document_number=data.kyc_document_number,
        bank_account_name=data.bank_account_name,
        bank_account_number=data.bank_account_number,
        bank_name=data.bank_name,
        bank_branch=data.bank_branch,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    try:
        with db.begin():
            db.add(seller)
        return SellerResponse.from_orm(seller)
    except IntegrityError as exc:
        db.rollback()
        error_message=str(exc.orig).lower()
        if "username" in error_message:
            raise error_handler(
                400,"Username already exists"
            ) 
        if "email" in error_message:
            raise error_message(
                400,"Email already exists"
            )
        if "phone number" in error_message:
            raise error_message(
                400,"phone already exists"
            )
        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "Invalid customer data"
        )


def admin_approve_account(
    db: Session,
    seller_id: int,
    seller_approved: SellerVerificationUpdate
):
    seller = db.query(Seller).filter(Seller.id == seller_id).one_or_none()
    if seller is None:
        raise error_handler(404, "Seller not found")
    seller.status = seller_approved.status
    seller.is_verified = seller_approved.is_verified
    seller.updated_at = datetime.utcnow()
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise error_handler(500,"Failed to update seller status")
    db.refresh(seller)
    return SellerResponse.from_orm(seller)

    
def update_seller_profile(
    db: Session,
    seller_update: SellerUpdate,
    current_user,
) -> SellerResponse:
    """Seller updates own profile."""

    seller = db.query(Seller).filter(Seller.id == current_user).first()
    if not seller:
        raise error_handler(404, "Seller not found")

    for key, value in seller_update.model_dump(exclude_unset=True).items():
        setattr(seller, key, value)

    seller.updated_at = datetime.utcnow()

    if (
        seller_update.kyc_document_type
        or seller_update.kyc_document_number
        or seller_update.kyc_document_url
        or seller_update.business_license_number
        or seller_update.business_license_url
    ):
        seller.is_verified = False
        seller.status = "PENDING"

    db.commit()
    db.refresh(seller)

    return SellerResponse.from_orm(seller)


def delete_seller_account(db: Session, current_user) -> dict:
    """Seller deletes own account."""

    seller = db.query(Seller).filter(Seller.id == current_user.id).first()
    
    if seller is None:
        raise error_handler(404, "Seller not found")
    


def delete_seller_by_admin(
    db: Session, seller_id: int, current_user
) -> dict:

    if not check_permission(current_user, "delete_seller_account"):
        raise error_handler(401, "Unauthorized access")

    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise error_handler(404, "Seller not found")
    try:
        db.delete(seller)
        db.commit()

        return {"message": f"Seller '{seller.username}' has been deleted."}
    except SQLAlchemyError:
        db.rollback()
        raise error_handler(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Account deletion failed"
        )
from fastapi import status
from jose import JWTError, ExpiredSignatureError
from jwt import ExpiredSignatureError, InvalidTokenError
def get_seller_from_token(token: str)->dict:
    try:
        seller_email = verify_token(token)
    except TokenResponse:
        raise error_handler(
            status.HTTP_401_UNAUTHORIZED,
            "Token has expired"
        )
    except InvalidTokenError:
        raise error_handler(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid authentication token"
        )
    return {"email": seller_email}
