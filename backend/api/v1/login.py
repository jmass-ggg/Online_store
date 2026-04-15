from uuid import UUID

from fastapi import APIRouter, Depends, Response, HTTPException, Request, status
from pydantic import BaseModel
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
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

router = APIRouter(prefix="/login", tags=["Login"])
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


COOKIE_NAME = "refresh_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
    )


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


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user, role = find_user_by_email(db, payload.email)

    if not user or not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Information",
        )
  
    access_token = create_access_token(user_id=user.id, role=role)
    refresh_token = create_refresh_token(db, user_id=user.id, role=role)

    set_refresh_cookie(response, refresh_token)
    return LoginResponse(access_token=access_token)


@router.post("/refresh", response_model=LoginResponse)
@limiter.limit("10/minute")
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    rt_raw = request.cookies.get(COOKIE_NAME)

    if not rt_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    rt: RefreshToken = verify_refresh_token(db, rt_raw)

    user = find_user_by_id_and_role(db, rt.owner_id, rt.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    rt.revoked = True
    db.commit()

    new_refresh = create_refresh_token(db, user_id=rt.owner_id, role=rt.role)
    set_refresh_cookie(response, new_refresh)

    new_access = create_access_token(user_id=user.id, role=rt.role)
    return LoginResponse(access_token=new_access)


@router.post("/logout")
@limiter.limit("20/minute")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    rt_raw = request.cookies.get(COOKIE_NAME)

    if rt_raw:
        try:
            rt = verify_refresh_token(db, rt_raw)
            rt.revoked = True
            db.commit()
        except HTTPException:
            pass

    delete_refresh_cookie(response)
    return {"message": "Logged out"}