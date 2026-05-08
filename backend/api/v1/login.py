from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.database import get_db
from backend.models.admin import AdminProfile
from backend.models.customer import CustomerProfile
from backend.models.refresh_token import RefreshToken
from backend.models.seller import Seller
from backend.models.user import User
from backend.utils.hashed import verify_password
from backend.utils.jwt import (
    REFRESH_COOKIE_NAME,
    clear_refresh_cookie,
    create_access_token,
    create_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    set_refresh_cookie,
    verify_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class LogoutResponse(BaseModel):
    message: str


def is_user_authorized(user: User) -> bool:
    if hasattr(user, "account_status"):
        return user.account_status == "ACTIVE"
    return True


def find_user_by_email(db: Session, email: str):
    admin = (
        db.query(AdminProfile)
        .join(AdminProfile.user)
        .filter(User.email == email)
        .first()
    )
    if admin:
        return admin.user, "Admin"

    seller = (
        db.query(Seller)
        .join(Seller.user)
        .filter(User.email == email)
        .first()
    )
    if seller:
        return seller.user, "Seller"

    customer = (
        db.query(CustomerProfile)
        .join(CustomerProfile.user)
        .filter(User.email == email)
        .first()
    )
    if customer:
        return customer.user, "Customer"

    return None, None


def find_user_by_id_and_role(db: Session, user_id: UUID, role: str):
    if role == "Admin":
        admin = (
            db.query(AdminProfile)
            .join(AdminProfile.user)
            .filter(User.id == user_id)
            .first()
        )
        return admin.user if admin else None

    if role == "Seller":
        seller = (
            db.query(Seller)
            .join(Seller.user)
            .filter(User.id == user_id)
            .first()
        )
        return seller.user if seller else None

    if role == "Customer":
        customer = (
            db.query(CustomerProfile)
            .join(CustomerProfile.user)
            .filter(User.id == user_id)
            .first()
        )
        return customer.user if customer else None

    return None


@router.post("/login", response_model=AccessTokenResponse)
# @limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest = Body(...),
    db: Session = Depends(get_db),
):
    user, role = find_user_by_email(db, payload.email)

    if not user or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not is_user_authorized(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not authorized to log in",
        )

    access_token = create_access_token(user_id=user.id, role=role)
    refresh_token = create_refresh_token(db, user_id=user.id, role=role)

    set_refresh_cookie(response, refresh_token)

    return AccessTokenResponse(
    access_token=access_token,
    token_type="bearer",
    role=role,
)


@router.post("/refresh", response_model=AccessTokenResponse)
@limiter.limit("10/minute")
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if not raw_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    refresh_token_record: RefreshToken = verify_refresh_token(db, raw_refresh_token)

    user = find_user_by_id_and_role(
        db=db,
        user_id=refresh_token_record.owner_id,
        role=refresh_token_record.role,
    )

    if not user:
        revoke_refresh_token(db, refresh_token_record)
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token owner",
        )

    if not is_user_authorized(user):
        revoke_refresh_token(db, refresh_token_record)
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is no longer authorized",
        )

    new_access_token = create_access_token(
        user_id=user.id,
        role=refresh_token_record.role,
    )

    new_refresh_token = rotate_refresh_token(db, refresh_token_record)

    set_refresh_cookie(response, new_refresh_token)

    return AccessTokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        role=refresh_token_record.role
    )


@router.post("/logout", response_model=LogoutResponse)
@limiter.limit("20/minute")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    raw_refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)

    if raw_refresh_token:
        try:
            refresh_token_record = verify_refresh_token(db, raw_refresh_token)
            revoke_refresh_token(db, refresh_token_record)
        except HTTPException:
            pass

    clear_refresh_cookie(response)

    return LogoutResponse(message="Logged out successfully")