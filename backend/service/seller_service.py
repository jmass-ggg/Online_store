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
from backend.schemas.customer import LoginResponse
from backend.schemas.seller import TokenResponse
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.utils.jwt import create_token, verify_token
from backend.utils.hashed import  verify_password
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler
from backend.utils.jwt import create_token, verify_token,create_refresh_token

def create_seller_application(db: Session, data: SellerApplicationCreate) -> SellerResponse:
    """Seller submits application. Default status = PENDING."""

    if db.query(Seller).filter(Seller.username == data.username).first():
        raise error_handler(302, "Username already exists")

    if db.query(Seller).filter(Seller.email == data.email).first():
        raise error_handler(302, "Email already registered")
    
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

    db.add(seller)
    db.commit()
    db.refresh(seller)

    return SellerResponse.from_orm(seller)


def seller_login(db: Session, form_data) -> TokenResponse:
    seller = db.query(Seller).filter(Seller.email == form_data.username).first()
    if not seller:
        raise error_handler(400, "Invalid credentials")

    if not verify_password(form_data.password, seller.hashed_password):
        raise error_handler(401, "Incorrect password")

    access_token = create_token({"email": seller.email})
    refresh_token = create_refresh_token(db, seller)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"  # <- required field
    )


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
    if not seller:
        raise error_handler(404, "Seller not found")

    db.delete(seller)
    db.commit()

    return {"message": "Your seller account has been deleted successfully."}


def delete_seller_by_admin(
    db: Session, seller_id: int, current_user
) -> dict:

    if not check_permission(current_user, "delete_seller_account"):
        raise error_handler(401, "Unauthorized access")

    seller = db.query(Seller).filter(Seller.id == seller_id).first()
    if not seller:
        raise error_handler(404, "Seller not found")

    db.delete(seller)
    db.commit()

    return {"message": f"Seller '{seller.username}' has been deleted."}


def get_seller_from_token(token: str):
    """Decode JWT and return seller identity."""
    seller_email = verify_token(token)
    return {"email": seller_email}
# {
#   "username": "johndoe",
#   "email": "joh_doe@example.com",
#   "phone_number": "876543210",
#   "password": "StrongPass123", 

#   "business_name": "John's Electronics",
#   "business_type": "Individual",
#   "business_address": "123 Main Street, Kathmandu, Nepal",

#   "kyc_document_type": "Passport",
#   "kyc_document_number": 12356789,

#   "bank_account_name": "John De",
#   "bank_account_number": 987654210,
#   "bank_name": "Nepal Bank",
#   "bank_branch": "Thamel Branch",

#   "status": "REJECTED",
#   "is_verified": false,
#   "role_name": "Seller"
# }
# {
#   "id": 2,
#   "username": "asdasd",
#   "email": "asdasd@example.com",
#   "phone_number": "8743210",
#   "status": "REJECTED",
#   "is_verified": false,
#   "kyc_document_type": "Passport",
#   "kyc_document_number": 123789,
#   "bank_account_name": "John sdfs",
#   "business_type": "Individual",
#   "business_address": "123 Main Street, Kathmandu, Nepal",
#   "bank_account_number": 9876210,
#   "bank_name": "Nepal Bank",
#   "bank_branch": "Thamel Branch",
#   "created_at": "2025-11-29T13:20:49.393242",
#   "updated_at": "2025-11-29T13:20:49.393249"
# }