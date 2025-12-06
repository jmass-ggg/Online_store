from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseSettings
import secrets

from backend.database import get_db
from backend.models.customer import Customer
from backend.models.admin import Admin
from backend.models.seller import Seller
from backend.models.refresh_token import RefreshToken
from backend.core.error_handler import error_handler
from backend.utils.auth import oauth2_scheme

# sdfsdf@example.com
# sdfsdfF


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()


# ---------------------------
# ACCESS TOKEN
# ---------------------------
def create_token(data: dict):
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload.update({
        "sub": payload.get("email"),
        "role": payload.get("role"),
        "exp": expire
    })

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")

        if not email or not role:
            raise error_handler(status.HTTP_401_UNAUTHORIZED, "Invalid token structure")

        return {"email": email, "role": role}

    except JWTError:
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")


# ---------------------------
# REFRESH TOKEN
# ---------------------------
REFRESH_EXP_DAYS = 7


def create_refresh_token(db: Session, user):
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(days=REFRESH_EXP_DAYS)

    new_rt = RefreshToken(
        token=token,
        user_id=user.id,
        expires_at=expiry
    )
    db.add(new_rt)
    db.commit()
    db.refresh(new_rt)

    return token


def verify_refresh_token(db: Session, token: str):
    rt = db.query(RefreshToken).filter(RefreshToken.token == token).first()

    if not rt:
        raise error_handler(401, "Invalid refresh token")

    if rt.expires_at < datetime.utcnow():
        db.delete(rt)
        db.commit()
        raise error_handler(401, "Refresh token expired")

    return rt.user_id
def get_current_user(token: str = Depends(oauth2_scheme)):
    return verify_token(token)


def get_current_customer(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user["role"] != "customer":
        raise error_handler(403, "Customer role required")

    person = db.query(Customer).filter(Customer.email == user["email"]).first()
    if not person:
        raise error_handler(404, "Customer not found")

    return person


def get_current_seller(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user["role"] != "seller":
        raise error_handler(403, "Seller role required")

    person = db.query(Seller).filter(Seller.email == user["email"]).first()
    if not person:
        raise error_handler(404, "Seller not found")

    return person


def get_current_admin(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user["role"] != "admin":
        raise error_handler(403, "Admin role required")

    person = db.query(Admin).filter(Admin.email == user["email"]).first()
    if not person:
        raise error_handler(404, "Admin not found")

    return person
