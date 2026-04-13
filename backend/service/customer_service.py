from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
from backend.models.customer import CustomerProfile
from backend.schemas.customer import CustomerRegisterRequest,CustomerProfileResponse,CustomerUpdate
from backend.service.user_service import ensure_user_not_exists,create_user_instance
from backend.api.v1.login import LoginResponse
from backend.utils.jwt import create_access_token, verify_token, create_refresh_token
from backend.utils.hashed import verify_password
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.core.error_handler import error_handler
from backend.models.email_token_verification import EmailTokenVerification
from backend.utils.seller_email_verification import (generate_email_token,hash_email_token,send_seller_verification_email,)
from datetime import datetime,timedelta
from sqlalchemy.orm import selectinload,joinedload

def create_new_verification(db:Session,customer:CustomerProfile):
    old_tokens=(
        db.query(EmailTokenVerification).filter(
            EmailTokenVerification.user_id == customer.user_id,
            EmailTokenVerification.used.is_(False)
        )
        .all()
    )
    for tokens in old_tokens:
        db.delete(tokens)
    raw_token = generate_email_token()
    token_hashed = hash_email_token(raw_token)
    
    verification=EmailTokenVerification(
         user_id=customer.user_id,
        token_hash=token_hashed,
        expired_at=datetime.utcnow() + timedelta(minutes=10),
        used=False,
    )
    db.add(verification)
    db.flush()
    return raw_token

def register_customer(
    db: Session,
    payload: CustomerRegisterRequest,
) -> CustomerProfileResponse:
    try:
        user = create_user_instance(
            db,
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )

        customer = CustomerProfile(
            user_id=user.id,
            is_email_verified=False,
            status="ACTIVE",
            role_name="Customer",
        )
        db.add(customer)
        db.flush()

        db.commit()
        db.refresh(user)
        db.refresh(customer)

        return CustomerProfileResponse.model_validate(customer)

    except HTTPException as e:
        db.rollback()
        print("HTTPException:", e.detail)
        raise

    except IntegrityError as e:
        db.rollback()
        print("IntegrityError:", str(e.orig))  
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.orig),   
        )

    except Exception as e:
        db.rollback()
        print("Unexpected error:", repr(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
        
from backend.models.user import User

def verify_user_email(token: str, db: Session) -> dict:
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

    seller = db.query(CustomerProfile).filter(CustomerProfile.user_id == user.id).first()
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found.",
        )

    user.is_email_verified = True
    verification.used = True

    db.commit()

    return {"message": "Seller email verified successfully."}


def customer_info_update(
    db: Session,
    user_update: CustomerUpdate,
    user_id: UUID,
) -> CustomerProfileResponse:
    user = (db.query(CustomerProfile).options(joinedload(CustomerProfile.user)).filter(CustomerProfile.user_id == user_id).one_or_none()
)
    if not user:
        raise error_handler(404, "User not found")

    user.username = user_update.username
    user.email = user_update.email
    user.phone_number = user_update.phone_number

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return CustomerProfile.model_validate(user)

    except IntegrityError as exc:
        db.rollback()
        error_message = str(exc.orig).lower()

        if "email" in error_message:
            raise error_handler(409, "Email already in use")

        if "username" in error_message:
            raise error_handler(409, "Username already in use")

        raise error_handler(400, "Invalid update data")

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(500, "Profile update failed")


def delete_account_by_owner(db: Session, current_id: UUID) -> dict:
    user = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_id).first()

    if not user:
        raise error_handler(404, "User not found")

    try:
        db.delete(user)
        db.commit()
        return {"message": "Your account has been deleted successfully."}

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(500, "Account deletion failed")


def get_user(token: str) -> dict:
    user_email = verify_token(token)
    return {"email": user_email}