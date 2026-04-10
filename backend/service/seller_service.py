from datetime import datetime, timedelta
from uuid import UUID
from typing import Any
import os
import shutil
from uuid import uuid4
from fastapi import BackgroundTasks, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload,joinedload
from backend.core.error_handler import error_handler

from backend.models.seller import (
    Seller,
    SellerVerification,
    AccountType,
    SellerEmailTokenVerification,
    SellerInformation,
    SellerBusinessAddress,
)
from backend.schemas.seller import (
    SellerRegister,
    SellerRegisterRead,
    SellerInforMationRead,
    SellerBusinessAddressCreate,
    SellerBusinessAddressRead,
    SellerVerificationUpdate,SellerDetail
)
from backend.service.auth_lookup_service import identity_exists
from backend.utils.seller_email_verification import (
    generate_email_token,
    hash_email_token,
    send_seller_verification_email,
)
from backend.utils.hashed import hashed_password as hashed_pwd

UPLOAD_FOLDER = "backend/important_document/"


def create_new_verification(db: Session, seller: Seller) -> str:
    old_token = (
        db.query(SellerEmailTokenVerification)
        .filter(
            SellerEmailTokenVerification.user_id == seller.id,
            SellerEmailTokenVerification.used == False,
        )
        .first()
    )

    if old_token:
        db.delete(old_token)
        db.commit()

    raw_token = generate_email_token()
    token_hashed = hash_email_token(raw_token)

    verification = SellerEmailTokenVerification(
        user_id=seller.id,
        token_hash=token_hashed,
        expired_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return raw_token

def seller_register(db: Session, data: SellerRegister, background_tasks: BackgroundTasks):
    email_check = identity_exists(db, email=data.email)
    if email_check["exists"] and email_check["role"] != "Seller":
        raise error_handler(400, f"Email already exists in {email_check['role']} account")

    username_check = identity_exists(db, username=data.username)
    if username_check["exists"]:
        raise error_handler(400, f"Username already exists in {username_check['role']} account")

    existing_seller = db.query(Seller).filter(Seller.email == data.email).first()

    if existing_seller is None:
        seller = Seller(
            username=data.username,
            email=data.email,
            phone_number=data.phone_number,
            hashed_password=hashed_pwd(data.hash_password),
            account_type=data.account_type,
        )
        db.add(seller)
        db.commit()
        db.refresh(seller)

        raw_token = create_new_verification(db, seller)
        background_tasks.add_task(send_seller_verification_email, seller.email, raw_token)
        return SellerRegisterRead.model_validate(seller)

    if existing_seller.is_email_verified:
        raise error_handler(400, "Seller is already registered, please login")

    raw_token = create_new_verification(db, existing_seller)
    background_tasks.add_task(
        send_seller_verification_email,
        existing_seller.email,
        raw_token,
    )
    return SellerRegisterRead.model_validate(existing_seller)

def verified_seller_email(token: str, db: Session):
    token_hash = hash_email_token(token)
    verification = (
        db.query(SellerEmailTokenVerification)
        .filter(SellerEmailTokenVerification.token_hash == token_hash)
        .first()
    )

    if verification is None:
        raise error_handler(status.HTTP_400_BAD_REQUEST, "Invalid verification token.")

    if verification.used:
        raise error_handler(status.HTTP_400_BAD_REQUEST, "This verification link was already used.")

    if datetime.utcnow() > verification.expired_at:
        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "Verification link expired. Please register again or resend verification.",
        )

    seller = db.query(Seller).filter(Seller.id == verification.user_id).first()
    if seller is None:
        raise error_handler(status.HTTP_400_BAD_REQUEST, "Seller not found")

    seller.is_email_verified = True
    verification.used = True
    db.commit()

    return {"email": "verified"}


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
    current_seller: Seller,
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

    existing_info = (
        db.query(SellerInformation)
        .filter(SellerInformation.user_id == current_seller.id)
        .first()
    )
    if existing_info:
        raise error_handler(400, "Seller information already exists")

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


def seller_information_read(db: Session, current_seller: Seller):
    seller_information = (
        db.query(SellerInformation)
        .filter(SellerInformation.user_id == current_seller.id)
        .first()
    )

    if not seller_information:
        raise error_handler(404, "Seller information not found")

    return SellerInforMationRead.model_validate(seller_information)


def seller_business_address_create(
    db: Session,
    current_seller: Seller,
    data: SellerBusinessAddressCreate,
):
    if not current_seller.is_email_verified:
        raise error_handler(400, "Seller email not verified")

    existing_address = (
        db.query(SellerBusinessAddress)
        .filter(SellerBusinessAddress.user_id == current_seller.id)
        .first()
    )
    if existing_address:
        raise error_handler(400, "Seller business address already exists")

    seller_address = SellerBusinessAddress(
        user_id=current_seller.id,
        country=data.country,
        province=data.province,
        district=data.district,
        area=data.area,
    )

    db.add(seller_address)
    db.commit()
    db.refresh(seller_address)

    return SellerBusinessAddressRead.model_validate(seller_address)


def seller_business_address_read(
    db: Session,
    current_seller: Seller,
):
    seller_address = (
        db.query(SellerBusinessAddress)
        .filter(SellerBusinessAddress.user_id == current_seller.id)
        .first()
    )

    if not seller_address:
        raise error_handler(404, "Seller business address not found")

    return SellerBusinessAddressRead.model_validate(seller_address)


def admin_approve_account(
    db: Session,
    seller_id: UUID,
    seller_approved: SellerVerificationUpdate,
):
    seller = db.query(Seller).filter(Seller.id == seller_id).one_or_none()

    if seller is None:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Seller not found")

    seller.status = seller_approved.status.value
    seller.is_verified = seller_approved.is_verified
    seller.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(seller)
    return SellerRegisterRead.model_validate(seller)

from backend.models.seller import Seller,SellerBusinessAddress,SellerEmailTokenVerification,SellerInformation
def get_seller_detail(db: Session, seller_id: UUID):
    seller = (
        db.query(Seller)
        .filter(Seller.id == seller_id)
        .options(
            selectinload(Seller.seller_information),
            selectinload(Seller.seller_business_address),
        )
        .first()
    )

    if not seller:
        raise error_handler(400, "Seller not found")

    if not seller.seller_information:
        raise error_handler(400, "Seller information not found")

    if not seller.seller_business_address:
        raise error_handler(400, "Seller business address not found")

    return SellerDetail(
        sellerDetail=SellerRegisterRead.model_validate(seller),
        sellerInformation=SellerInforMationRead.model_validate(seller.seller_information[0]),
        sellerAddress=SellerBusinessAddressRead.model_validate(seller.seller_business_address[0]),
    )