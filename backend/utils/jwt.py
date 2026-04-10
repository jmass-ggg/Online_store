from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Literal, TypedDict, Union

from jose import jwt
from jose.exceptions import JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic_settings import BaseSettings
from sqlalchemy.orm import Session

from backend.core.error_handler import error_handler
from backend.database import get_db
from backend.models.admin import Admin
from backend.models.customer import Customer
from backend.models.refresh_token import RefreshToken
from backend.models.seller import Seller


RoleType = Literal["Admin", "Seller", "Customer"]


class TokenPayload(TypedDict):
    email: str
    role: RoleType


class CurrentUser(TypedDict):
    email: str
    role: RoleType
    user: Union[Admin, Seller, Customer]


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    database_url: str

    class Config:
        env_file = ".env"


settings = Settings()
bearer_scheme = HTTPBearer()


def _now() -> datetime:
    return datetime.utcnow()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_user_by_role(db: Session, email: str, role: RoleType):
    if role == "Admin":
        return db.query(Admin).filter(Admin.email == email).first()
    if role == "Seller":
        return db.query(Seller).filter(Seller.email == email).first()
    if role == "Customer":
        return db.query(Customer).filter(Customer.email == email).first()
    return None


def create_access_token(email: str, role: RoleType) -> str:
    payload = {
        "sub": email,
        "role": role,
        "type": "access",
        "iat": int(_now().timestamp()),
        "exp": _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "access":
            raise error_handler(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid access token type",
            )

        email = payload.get("sub")
        role = payload.get("role")

        if not email or not role:
            raise error_handler(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid token payload",
            )

        if role not in ("Admin", "Seller", "Customer"):
            raise error_handler(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid user role in token",
            )

        return {"email": email, "role": role}

    except JWTError:
        raise error_handler(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
        )


def create_refresh_token(db: Session, user_id: int, role: RoleType) -> str:
    raw = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw)

    rt = RefreshToken(
        token_hash=token_hash,
        role=role,
        owner_id=user_id,
        expires_at=_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )

    db.add(rt)
    db.commit()
    db.refresh(rt)

    return raw


def verify_refresh_token(db: Session, token: str) -> RefreshToken:
    token_hash = _hash_token(token)

    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if not rt:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if rt.revoked:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    if rt.expires_at < _now():
        rt.revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired")

    return rt


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> CurrentUser:
    payload = verify_token(token)
    email = payload["email"]
    role = payload["role"]

    user = _get_user_by_role(db, email=email, role=role)
    if not user:
        raise error_handler(status.HTTP_404_NOT_FOUND, f"{role} not found")

    return {
        "email": email,
        "role": role,
        "user": user,
    }

def get_current_customer(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user["role"] != "Customer":
        raise error_handler(403, "Customer role required")

    customer = db.query(Customer).filter(Customer.email == user["email"]).first()
    if not customer:
        raise error_handler(404, "Customer not found")

    return customer


def get_current_seller(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user["role"] != "Seller":
        raise error_handler(403, "Seller role required")

    seller = db.query(Seller).filter(Seller.email == user["email"]).first()
    if not seller:
        raise error_handler(404, "Seller not found")

    return seller


def get_current_admin(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user["role"] != "Admin":
        raise error_handler(403, "Admin role required")

    admin = db.query(Admin).filter(Admin.email == user["email"]).first()
    if not admin:
        raise error_handler(404, "Admin not found")

    return admin
