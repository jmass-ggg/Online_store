from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from backend.core.error_handler import error_handler
from backend.models.customer import CustomerProfile
from backend.models.email_token_verification import EmailTokenVerification
from backend.models.user import User
from backend.schemas.customer import (
    CustomerRegisterRequest,
    CustomerProfileResponse,
    CustomerUpdate,
)
from backend.service.user_service import create_user_instance
from backend.utils.seller_email_verification import (
    generate_email_token,
    hash_email_token,
    send_customer_verification_email,
)


def create_new_verification(db: Session, customer: CustomerProfile) -> str:
    old_tokens = (
        db.query(EmailTokenVerification)
        .filter(
            EmailTokenVerification.user_id == customer.user_id,
            EmailTokenVerification.used.is_(False),
        )
        .all()
    )

    for token in old_tokens:
        db.delete(token)

    raw_token = generate_email_token()
    token_hashed = hash_email_token(raw_token)

    verification = EmailTokenVerification(
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
    background_tasks: BackgroundTasks,
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
            
            status="ACTIVE",
            role_name="Customer",
        )
        db.add(customer)
        db.flush()

        raw_token = create_new_verification(db, customer)

        db.commit()
        db.refresh(customer)

        background_tasks.add_task(
            send_customer_verification_email,  
            user.email,
            raw_token,
        )

        return CustomerProfileResponse.model_validate(customer)

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.orig),
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


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

    customer = (
        db.query(CustomerProfile)
        .filter(CustomerProfile.user_id == user.id)
        .first()
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found.",
        )

    user.is_email_verified = True
    verification.used = True

    db.commit()

    return {"message": "Customer email verified successfully."}


def customer_info_update(
    db: Session,
    user_update: CustomerUpdate,
    user_id: UUID,
) -> CustomerProfileResponse:
    customer = (
        db.query(CustomerProfile)
        .options(joinedload(CustomerProfile.user))
        .filter(CustomerProfile.user_id == user_id)
        .one_or_none()
    )

    if not customer:
        raise error_handler(404, "User not found")

    if user_update.username is not None:
        customer.user.username = user_update.username
    if user_update.email is not None:
        customer.user.email = user_update.email
    
    try:
        db.commit()
        db.refresh(customer)
        return CustomerProfileResponse.model_validate(customer)

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
    user = (
        db.query(User)
        .options(joinedload(User.customer_profile))
        .filter(User.id == current_id)
        .first()
    )

    if not user:
        raise error_handler(404, "User not found")

    try:
        db.delete(user)
        db.commit()
        return {"message": "Your account has been deleted successfully."}

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(500, "Account deletion failed")