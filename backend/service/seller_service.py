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
from backend.models.seller import Seller
from backend.models.seller_personal_information import SellerPersonalInformation
from backend.schemas.seller import (
    SellerPersonalInformationCreate,
    SellerPersonalInformationRead,SellerBusinessAddressCreate
    ,SellerBusinessAddressRead,SellerRegisterRequest,
    SellerRegisterResponse,SellerRegisterRead,
    SellerVerificationUpdate,SellerDetail
)
from backend.service.user_service import create_user_instance
from backend.models.user import User
from backend.utils.seller_email_verification import (
    generate_email_token,
    hash_email_token,
    send_seller_verification_email,
)

from backend.models.seller_business_address import SellerBusinessAddress
from backend.models.seller_personal_information import SellerPersonalInformation
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from backend.utils.hashed import hashed_password as hashed_pwd

UPLOAD_FOLDER = "backend/important_document/"


def create_new_verification(db: Session, seller: Seller) -> str:
    old_tokens = (
        db.query(EmailTokenVerification)
        .filter(
            EmailTokenVerification.user_id == seller.user_id,
            EmailTokenVerification.used.is_(False),
        )
        .all()
    )

    for token in old_tokens:
        db.delete(token)

    raw_token = generate_email_token()
    token_hashed = hash_email_token(raw_token)

    verification = EmailTokenVerification(
        user_id=seller.user_id,
        token_hash=token_hashed,
        expired_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
    )
    db.add(verification)
    db.flush()

    return raw_token

def save_upload_file(file: UploadFile, upload_folder: str = UPLOAD_FOLDER) -> str:
    os.makedirs(upload_folder, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(upload_folder, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return filename

def register_seller(
    db: Session,
    payload: SellerRegisterRequest,
    background_tasks: BackgroundTasks,
) -> SellerRegisterResponse:
    try:
        

        user = create_user_instance(
            db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )

        seller = Seller(
            user_id=user.id,
            account_type=payload.account_type.value,
            status="PENDING",
            is_verified=False,
            role_name="Seller",
        )
        db.add(seller)
        db.flush()

        raw_token = create_new_verification(db, seller)

        db.commit()
        db.refresh(user)
        db.refresh(seller)

        background_tasks.add_task(send_seller_verification_email, user.email, raw_token)

        return SellerRegisterResponse(
            message="Seller registered successfully. Please verify your email first.",
            user_id=user.id,
            seller_id=seller.id,
            username=user.username,
            email=user.email,
            role_name=seller.role_name,
            account_type=seller.account_type,
            status=seller.status,
            is_verified=seller.is_verified,
            is_email_verified=user.is_email_verified,
        )
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not register seller because of duplicate data.",
        )
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while registering seller.",
        )
from backend.models.email_token_verification import EmailTokenVerification

def verify_seller_email(token: str, db: Session) -> dict:
    token_hash = hash_email_token(token)

    verification = (
        db.query(EmailTokenVerification)
        .filter(EmailTokenVerification.token_hash == token_hash)
        .first()
    )

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token.",
        )

    if verification.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link was already used.",
        )

    if datetime.utcnow() > verification.expired_at.replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link expired. Please resend verification.",
        )

    user = db.query(User).filter(User.id == verification.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    seller = db.query(Seller).filter(Seller.user_id == user.id).first()
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    user.is_email_verified = True
    verification.used = True

    db.commit()

    return {"message": "Seller email verified successfully."}


def seller_information_fill(
    db: Session,
    current_seller: Seller,
    legal_name: str,
    pan_number: str,
    account_name: str,
    account_number: str,
    bank_name: str,
    branch_name: str,
    business_document_photo: UploadFile,
    cheque_photo: UploadFile,
) -> SellerPersonalInformationRead:
    seller = (
        db.query(Seller)
        .options(joinedload(Seller.user))
        .filter(Seller.id == current_seller.id)
        .one_or_none()
    )

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    if not seller.user.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="Please verify seller email before adding seller information.",
        )

    existing_info = (
        db.query(SellerPersonalInformation)
        .filter(SellerPersonalInformation.seller_id == seller.id)
        .first()
    )
    if existing_info:
        raise HTTPException(status_code=400, detail="Seller information already exists")

    business_document_photo_filename = save_upload_file(business_document_photo, UPLOAD_FOLDER)
    cheque_photo_filename = save_upload_file(cheque_photo, UPLOAD_FOLDER)

    seller_information = SellerPersonalInformation(
        seller_id=seller.id,
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

    return SellerPersonalInformationRead.model_validate(seller_information)


def seller_information_read(
    db: Session,
    current_seller: Seller,
) -> SellerPersonalInformationRead:
    seller_information = (
        db.query(SellerPersonalInformation)
        .filter(SellerPersonalInformation.seller_id == current_seller.id)
        .first()
    )

    if not seller_information:
        raise HTTPException(status_code=404, detail="Seller information not found")

    return SellerPersonalInformationRead.model_validate(seller_information)

def seller_business_address_create(
    db: Session,
    current_seller: Seller,
    data: SellerBusinessAddressCreate,
) -> SellerBusinessAddressRead:
    seller = (
        db.query(Seller)
        .options(joinedload(Seller.user))
        .filter(Seller.id == current_seller.id)
        .one_or_none()
    )

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    if not seller.user.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="Please verify seller email before adding business address.",
        )

    existing_address = (
        db.query(SellerBusinessAddress)
        .filter(SellerBusinessAddress.seller_id == seller.id)
        .first()
    )
    if existing_address:
        raise HTTPException(status_code=400, detail="Seller business address already exists")

    seller_address = SellerBusinessAddress(
        seller_id=seller.id,
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
) -> SellerBusinessAddressRead:
    seller_address = (
        db.query(SellerBusinessAddress)
        .filter(SellerBusinessAddress.seller_id == current_seller.id)
        .first()
    )

    if not seller_address:
        raise HTTPException(status_code=404, detail="Seller business address not found")

    return SellerBusinessAddressRead.model_validate(seller_address)


def admin_approve_account(
    db: Session,
    seller_id: UUID,
    seller_approved: SellerVerificationUpdate,
):
    seller = (
        db.query(Seller)
        .options(joinedload(Seller.user))
        .filter(Seller.id == seller_id)
        .one_or_none()
    )

    if seller is None:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Seller not found")

    seller.status = seller_approved.status.value
    seller.is_verified = seller_approved.is_verified
    seller.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(seller)
    return SellerRegisterRead.model_validate(seller)

def get_seller_detail(db: Session, seller_id: UUID):
    seller = (
        db.query(Seller)
        .options(
            joinedload(Seller.user),
            selectinload(Seller.personal_information),
            selectinload(Seller.business_addresses),
        )
        .filter(Seller.id == seller_id)
        .first()
    )

    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")

    if not seller.personal_information:
        raise HTTPException(status_code=404, detail="Seller information not found")

    if not seller.business_addresses:
        raise HTTPException(status_code=404, detail="Seller business address not found")

    return SellerDetail(
        seller_detail=SellerRegisterRead(
            seller_id=seller.id,
            user_id=seller.user_id,
            username=seller.user.username,
            email=seller.user.email,
            account_type=seller.account_type,
            status=seller.status,
            is_verified=seller.is_verified,
            is_email_verified=seller.user.is_email_verified,
            role_name=seller.role_name,
        ),
        seller_information=SellerPersonalInformationRead.model_validate(seller.personal_information[0]),
        seller_address=SellerBusinessAddressRead.model_validate(seller.business_addresses[0]),
    )