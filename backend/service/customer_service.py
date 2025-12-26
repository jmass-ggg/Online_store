from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db
from backend.models.customer import Customer
from backend.models.role import Roles
from backend.schemas.customer import (
    CustomerCreate,
    CustomerRead,
    TokenResponse,
    CustomerUpdate,
    LoginResponse
)
from backend.utils.jwt import create_token, verify_token,create_refresh_token
from backend.utils.hashed import  verify_password
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler
from backend.models.refresh_token import RefreshToken
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

def create_customer(db: Session, username: str, email: str, 
                    password: str,phone_number:str,address:str,) -> CustomerRead:
    """Register a new user with hashed password and unique username/email."""

    new_user = Customer(
        username=username,
        email=email,
        hashed_password=hashed_pwd(password),
        phone_number=phone_number,
        address=address,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    try:
        with db.begin():
            db.add(new_user)
        return CustomerRead.from_orm(new_user)
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
        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "Invalid customer data"
        )

def customer_login(db: Session, form_data) -> LoginResponse:
    try:
        user=db.query(Customer).filter(Customer.email == form_data.username).one_or_none()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise error_handler(404,"User not found")
        access_token = create_token({"email": user.email})
        refresh_token = create_refresh_token(db, user)
        return LoginResponse(access_token=access_token,refresh_token=refresh_token)
    except SQLAlchemyError:
        raise error_handler(status.HTTP_404_NOT_FOUND,"Authentication failed")
    

def customer_info_update(
    db: Session,  user_update: CustomerUpdate,user_id:int
) -> CustomerRead:
    """Update user details (self-profile edit)."""
    user = (
        db.query(Customer)
        .filter(Customer.id == user_id)
        .one_or_none()
    )

    if not user:
        raise error_handler(
            status.HTTP_404_NOT_FOUND,
            "User not found"
        )

    try:
        with db.begin():
            db.add(user)

        db.refresh(user)
        return CustomerRead.from_orm(user)

    except IntegrityError as exc:
        db.rollback()

        # Database is the source of truth
        if "email" in str(exc.orig):
            raise error_handler(
                status.HTTP_409_CONFLICT,
                "Email already in use"
            )

        if "username" in str(exc.orig):
            raise error_handler(
                status.HTTP_409_CONFLICT,
                "Username already in use"
            )

        raise error_handler(
            status.HTTP_400_BAD_REQUEST,
            "Invalid update data"
        )

    except SQLAlchemyError:
        raise error_handler(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Profile update failed"
        )

def delete_account_by_owner(db: Session, current_user: Customer):
    """Allow a user to delete their own account."""

    
    user=db.query(Customer).filter(Customer.id == current_user.id).one_or_none()
    if not user:
        raise error_handler(status.HTTP_404_NOT_FOUND,"User not found")
    try:
        db.delete(user)
        db.commit()
        return {"message": "Your account has been deleted successfully."}

    except SQLAlchemyError:
        db.rollback()
        # Log internally, never leak DB errors to client
        raise error_handler(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Account deletion failed"
        )



def get_user(token: str) -> dict:
    """Decode JWT and return user identity."""
    user_email = verify_token(token)
    return {"email": user_email}
