from datetime import datetime
from typing import Any

from fastapi import status
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.core.error_handler import error_handler
from backend.core.permission import check_permission
from backend.models.seller import Seller, SellerVerification
from backend.schemas.seller import (
    SellerApplicationCreate,
    SellerResponse,
    SellerUpdate,
    SellerVerificationUpdate,
)
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.utils.jwt import verify_token
from uuid import UUID

def create_seller_application(db: Session, data: SellerApplicationCreate) -> SellerResponse:
    now = datetime.utcnow()

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
        created_at=now,
        updated_at=now,
        status=SellerVerification.PENDING.value,
        is_verified=False,
    )

    try:
        db.add(seller)
        db.commit()
        db.refresh(seller)
        return SellerResponse.model_validate(seller)

    except IntegrityError as exc:
        db.rollback()
        message = str(exc.orig).lower()

        if "username" in message:
            raise error_handler(status.HTTP_400_BAD_REQUEST, "Username already exists")
        if "email" in message:
            raise error_handler(status.HTTP_400_BAD_REQUEST, "Email already exists")
        if "phone_number" in message or "phone number" in message:
            raise error_handler(status.HTTP_400_BAD_REQUEST, "Phone number already exists")

        raise error_handler(status.HTTP_400_BAD_REQUEST, "Invalid seller data")

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to create seller account")


def admin_approve_account(
    db: Session,
    seller_id:UUID,
    seller_approved: SellerVerificationUpdate,
) -> SellerResponse:
    seller = db.query(Seller).filter(Seller.id == seller_id).one_or_none()

    if seller is None:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Seller not found")

    seller.status = seller_approved.status.value
    seller.is_verified = seller_approved.is_verified
    seller.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(seller)
        return SellerResponse.model_validate(seller)

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update seller status")


def update_seller_profile(
    db: Session,
    seller_update: SellerUpdate,
    current_user: Any,
) -> SellerResponse:
    seller = db.query(Seller).filter(Seller.id == current_user.id).first()

    if not seller:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Seller not found")

    update_data = seller_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(seller, key, value)

    seller.updated_at = datetime.utcnow()

    if any(
        [
            seller_update.kyc_document_type,
            seller_update.kyc_document_number,
            seller_update.kyc_document_url,
            seller_update.business_license_number,
            seller_update.business_license_url,
        ]
    ):
        seller.is_verified = False
        seller.status = SellerVerification.PENDING.value

    try:
        db.commit()
        db.refresh(seller)
        return SellerResponse.model_validate(seller)

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to update seller profile")


def delete_seller_account(db: Session, current_user: Any) -> dict:
    seller = db.query(Seller).filter(Seller.id == current_user.id).first()

    if seller is None:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Seller not found")

    try:
        db.delete(seller)
        db.commit()
        return {"message": f"Seller '{seller.username}' deleted successfully."}

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR, "Account deletion failed")


def delete_seller_by_admin(db: Session, seller_id, current_user: Any) -> dict:
    if not check_permission(current_user, "delete_seller_account"):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized access")

    seller = db.query(Seller).filter(Seller.id == seller_id).first()

    if not seller:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Seller not found")

    try:
        db.delete(seller)
        db.commit()
        return {"message": f"Seller '{seller.username}' has been deleted."}

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR, "Account deletion failed")


def get_seller_from_token(token: str) -> dict:
    try:
        seller_email = verify_token(token)
        return {"email": seller_email}

    except ExpiredSignatureError:
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Token has expired")

    except InvalidTokenError:
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Invalid authentication token")