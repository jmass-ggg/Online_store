from fastapi import APIRouter, Depends, Response, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from backend.database import get_db
from backend.utils.jwt import create_access_token, create_refresh_token, verify_refresh_token
from backend.utils.hashed import verify_password

from backend.models.admin import Admin
from backend.models.seller import Seller
from backend.models.customer import Customer
from backend.models.refresh_token import RefreshToken

router = APIRouter(prefix="/login", tags=["Login"])


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
        secure=False,           
        samesite="lax",         
        max_age=COOKIE_MAX_AGE,
        path="/",               
    )

def delete_refresh_cookie(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",               
    )


@router.post("/login", response_model=LoginResponse)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form_data.username
    password = form_data.password

    user = db.query(Admin).filter(Admin.email == email).first()
    role = "Admin"

    if not user:
        user = db.query(Seller).filter(Seller.email == email).first()
        role = "Seller"

    if not user:
        user = db.query(Customer).filter(Customer.email == email).first()
        role = "Customer"

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    access = create_access_token(email=user.email, role=role)
    refresh_token = create_refresh_token(db, user_id=user.id, role=role)

    set_refresh_cookie(response, refresh_token)

    return LoginResponse(access_token=access)


@router.post("/refresh", response_model=LoginResponse)
def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    rt_raw = request.cookies.get(COOKIE_NAME)
    if not rt_raw:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    rt: RefreshToken = verify_refresh_token(db, rt_raw)

    if rt.role == "Admin":
        user = db.query(Admin).filter(Admin.id == rt.owner_id).first()
    elif rt.role == "Seller":
        user = db.query(Seller).filter(Seller.id == rt.owner_id).first()
    else:
        user = db.query(Customer).filter(Customer.id == rt.owner_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

  
    rt.revoked = True
    db.commit()

    new_refresh = create_refresh_token(db, user_id=rt.owner_id, role=rt.role)
    set_refresh_cookie(response, new_refresh)

    new_access = create_access_token(email=user.email, role=rt.role)
    return LoginResponse(access_token=new_access)


@router.post("/logout")
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
    return {"message": "logged out"}
