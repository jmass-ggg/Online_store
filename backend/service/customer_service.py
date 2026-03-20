from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.models.customer import Customer
from backend.schemas.customer import CustomerRead, CustomerUpdate
from backend.api.v1.login import LoginResponse
from backend.utils.jwt import create_access_token, verify_token, create_refresh_token
from backend.utils.hashed import verify_password
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.core.error_handler import error_handler


def create_customer(
    db: Session,
    username: str,
    email: str,
    password: str,
    phone_number: str,
) -> CustomerRead:
    new_user = Customer(
        username=username,
        email=email,
        hashed_password=hashed_pwd(password),
        phone_number=phone_number,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return CustomerRead.model_validate(new_user)

    except IntegrityError as exc:
        db.rollback()
        error_message = str(exc.orig).lower()

        if "username" in error_message:
            raise error_handler(400, "Username already exists")

        if "email" in error_message:
            raise error_handler(400, "Email already exists")

        raise error_handler(400, "Invalid customer data")

    except SQLAlchemyError:
        db.rollback()
        raise error_handler(500, "Failed to create customer")


def customer_login(db: Session, form_data) -> LoginResponse:
    try:
        user = db.query(Customer).filter(Customer.email == form_data.username).one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise error_handler(404, "User not found")

        access_token = create_access_token({"email": user.email})
        refresh_token = create_refresh_token(db, user)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    except SQLAlchemyError:
        raise error_handler(404, "Authentication failed")


def customer_info_update(
    db: Session,
    user_update: CustomerUpdate,
    user_id: UUID,
) -> CustomerRead:
    user = db.query(Customer).filter(Customer.id == user_id).one_or_none()

    if not user:
        raise error_handler(404, "User not found")

    user.username = user_update.username
    user.email = user_update.email
    user.phone_number = user_update.phone_number

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return CustomerRead.model_validate(user)

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


def delete_account_by_owner(db: Session, current_user: Customer) -> dict:
    user = db.query(Customer).filter(Customer.id == current_user.id).one_or_none()

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