from datetime import datetime
from typing import Any

from fastapi import status,BackgroundTasks,Depends,UploadFile
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.core.error_handler import error_handler
from backend.core.permission import check_permission
from backend.models.seller import Seller, SellerVerification,AccountType,SellerEmailTokenVerification,SellerInformation
from backend.schemas.seller import (
    SellerApplicationCreate,
    SellerResponse,
    SellerUpdate,SellerInforMation,SellerInforMationRead,
    SellerVerificationUpdate,SellerRegister,SellerRegisterRead
)
from backend.utils.seller_email_verification import generate_email_token,hash_email_token,send_seller_verification_email
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.utils.jwt import verify_token
from uuid import UUID
from datetime import timedelta

UPLOAD_FOLDER="backend/important_document/"

def create_new_verification(db:Session,seller:Seller)->str:
    old_token=db.query(SellerEmailTokenVerification).filter(SellerEmailTokenVerification.user_id == seller.id,SellerEmailTokenVerification.used == False).first()
    if old_token:
        db.delete(old_token)
        db.commit()
    raw_token=generate_email_token()
    token_hashed=hash_email_token(raw_token)
    
    verification=SellerEmailTokenVerification(
        user_id=seller.id,
        token_hash=token_hashed,
        expired_at=datetime.utcnow() + timedelta(minutes=10),
        used=False
        
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return raw_token
    

def seller_register(db:Session,data:SellerRegister,background_tasks: BackgroundTasks):
    existing_seller=db.query(Seller).filter(Seller.email == data.email).first()
    if existing_seller is None:
        seller=Seller(
            username=data.username,
            email=data.email,
            phone_number=data.phone_number,
            hashed_password=hashed_pwd(data.hash_password),
            account_type=data.account_type
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)
        
        raw_token=create_new_verification(db,seller)
        background_tasks.add_task(
            send_seller_verification_email,seller.email,raw_token,
        )
        return SellerRegisterRead.model_validate(seller)
    if existing_seller.is_email_verified:
        raise error_handler(400,"Seller is already register please Login")
    raw_token=create_new_verification(db,existing_seller)
    background_tasks.add_task(
        send_seller_verification_email,
        existing_seller.email,
        raw_token,
    )
    return SellerRegisterRead.model_validate(existing_seller)

def verified_seller_email(token:str,db:Session,):
    token_hash=hash_email_token(token)
    verification=db.query(SellerEmailTokenVerification).filter(SellerEmailTokenVerification.token_hash == token_hash).first()
    if verification is None:
        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "Invalid verification token."
        )

    if verification.used:
        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "This verification link was already used."
        )

    if datetime.utcnow() > verification.expired_at:
        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "Verification link expired. Please register again or resend verification."
        )
    seller=db.query(Seller).filter(Seller.id == verification.user_id).first()
    if seller is None:
        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "Seller not found"
        )
    seller.is_email_verified=True
    verification.used=True
    db.commit()
    return {"email ":"verified"}
import os
import shutil
from   uuid import uuid4
def save_upload_file(file: UploadFile, upload_folder: str) -> str:
    os.makedirs(upload_folder, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(upload_folder, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return filename
def seller_information_fill(
    db: Session,
    current_seller,
    legal_name: str,
    pan_number: str,
    account_name: str,
    account_number: str,
    bank_name: str,
    branch_name: str,
    business_document_photo_filename: str,
    cheque_photo_filename: str,
):
    if not current_seller.is_email_verified:
        raise error_handler(400, "Seller email not verified")

    seller_information = SellerInformation(
        user_id=current_seller.id,
        legal_name=legal_name,
        pan_number=pan_number,
        business_document_photo=f"/important_document/{business_document_photo_filename}",
        account_name=account_name,
        account_number=account_number,
        bank_name=bank_name,
        branch_name=branch_name,
        cheque_photo=f"/important_document/{cheque_photo_filename}",
    )

    db.add(seller_information)
    db.commit()
    db.refresh(seller_information)

    return SellerInforMationRead.model_validate(seller_information)

def seller_information_read(
    db:Session,current_seller:Seller
):
    seller_information=db.query(SellerInformation).filter(SellerInformation.user_id == current_seller.id).first()
    if not seller_information:
        raise error_handler(
            400,"Seller information not found"
        )
    if not current_seller.is_verified:
        raise error_handler(
            400,"Seller  not verified"
        )
    return SellerInforMationRead.model_validate(seller_information)

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