from fastapi import APIRouter, Depends, Response, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.database import get_db
from backend.utils.jwt import create_access_token, create_refresh_token, verify_refresh_token
from backend.utils.hashed import verify_password

from backend.models.admin import Admin
from backend.models.seller import Seller
from backend.models.customer import Customer
from backend.models.refresh_token import RefreshToken
from backend.service.auth_lookup_service import find_user_by_email

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


def set_refresh_cookie(response: Response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,      # localhost only
        samesite="lax",    # localhost only
        max_age=COOKIE_MAX_AGE,
        path="/",
    )


def delete_refresh_cookie(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
    )


def find_user_by_id_and_role(db: Session, owner_id, role: str):
    if role == "Admin":
        return db.query(Admin).filter(Admin.id == owner_id).first()
    if role == "Seller":
        return db.query(Seller).filter(Seller.id == owner_id).first()
    if role == "Customer":
        return db.query(Customer).filter(Customer.id == owner_id).first()
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

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    access_token = create_access_token(email=user.email, role=role)
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
        raise HTTPException(status_code=401, detail="Missing refresh token")

    rt: RefreshToken = verify_refresh_token(db, rt_raw)

    user = find_user_by_id_and_role(db, rt.owner_id, rt.role)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rt.revoked = True
    db.commit()

    new_refresh = create_refresh_token(db, user_id=rt.owner_id, role=rt.role)
    set_refresh_cookie(response, new_refresh)

    new_access = create_access_token(email=user.email, role=rt.role)
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