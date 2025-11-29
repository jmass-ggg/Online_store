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

def create_customer(db: Session, username: str, email: str, 
                    password: str,phone_number:str,address:str,) -> CustomerRead:
    """Register a new user with hashed password and unique username/email."""

    if db.query(Customer).filter(Customer.username == username).first():
        raise error_handler(status.HTTP_302_FOUND, "Username already exists")

    if db.query(Customer).filter(Customer.email == email).first():
        raise error_handler(status.HTTP_302_FOUND, "Email already registered")

    new_user = Customer(
        username=username,
        email=email,
        hashed_password=hashed_pwd(password),
        phone_number=phone_number,
        address=address,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return CustomerRead.from_orm(new_user)

def customer_login(db: Session, form_data: OAuth2PasswordRequestForm) -> LoginResponse:
    """Authenticate user and return JWT access token."""

    user = db.query(Customer).filter(Customer.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise error_handler(status.HTTP_400_BAD_REQUEST, "Invalid credentials")

    access_token = create_token({"email": user.email})
    refresh_token, exp = create_refresh_token()
    db_refresh = RefreshToken(
    token=refresh_token,
    user_id=user.id,   
    expires_at=exp
    )

    db.add(db_refresh)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
        
    }

def customer_info_update(
    db: Session,  user_update: CustomerUpdate,current_user
) -> CustomerRead:
    """Update user details (self-profile edit)."""

    user = db.query(Customer).filter(Customer.id == current_user).first()
    if not user:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Customer not found")

    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return CustomerRead.from_orm(user)



def delete_account_by_owner(db: Session, current_user: Customer):
    """Allow a user to delete their own account."""

    user = db.query(Customer).filter(Customer.id == current_user.id).first()
    if not user :
        raise error_handler(status.HTTP_404_NOT_FOUND, "Customer not found")

    db.delete(user)
    db.commit()

    return {"message": "Your account has been deleted successfully."}

def delete_account_by_admin(
    customer_id: int, db: Session, current_user: Customer
) -> dict:
    """Allow an admin to delete another user's account."""

    if not check_permission(current_user,"delete_other_account"):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized access")

    user = db.query(Customer).filter(Customer.id == customer_id).first()
    if not user:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Customer not found")

    db.delete(user)
    db.commit()

    return {"message": f"Customer '{user.username}' has been deleted."}

def get_user(token: str) -> dict:
    """Decode JWT and return user identity."""
    user_email = verify_token(token)
    return {"email": user_email}
