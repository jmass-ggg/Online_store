from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal, TypedDict, Union
from uuid import UUID

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from pydantic_settings import BaseSettings
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models.admin import AdminProfile
from backend.models.customer import CustomerProfile
from backend.models.refresh_token import RefreshToken
from backend.models.seller import Seller
from backend.models.user import User


RoleType = Literal["Admin", "Seller", "Customer"]


class TokenPayload(TypedDict):
    user_id: UUID
    role: RoleType


class CurrentUser(TypedDict):
    user_id: UUID
    role: RoleType
    user: Union[AdminProfile, Seller, CustomerProfile]


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

REFRESH_COOKIE_NAME = "refresh_token"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=False,  # change to True in production with HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
    )


def _get_user_by_role(db: Session, user_id: UUID, role: RoleType):
    if role == "Admin":
        return (
            db.query(AdminProfile)
            .join(AdminProfile.user)
            .options(joinedload(AdminProfile.user))
            .filter(User.id == user_id)
            .first()
        )

    if role == "Seller":
        return (
            db.query(Seller)
            .join(Seller.user)
            .options(joinedload(Seller.user))
            .filter(User.id == user_id)
            .first()
        )

    if role == "Customer":
        return (
            db.query(CustomerProfile)
            .join(CustomerProfile.user)
            .options(joinedload(CustomerProfile.user))
            .filter(User.id == user_id)
            .first()
        )

    return None


def create_access_token(user_id: UUID, role: RoleType) -> str:
    now = _now()
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token type",
            )

        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        if role not in ("Admin", "Seller", "Customer"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user role in token",
            )

        return {"user_id": UUID(user_id), "role": role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def create_refresh_token(db: Session, user_id: UUID, role: RoleType) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)

    refresh_token = RefreshToken(
        token_hash=token_hash,
        role=role,
        owner_id=user_id,
        expires_at=_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)

    return raw_token


def verify_refresh_token(db: Session, token: str) -> RefreshToken:
    token_hash = _hash_token(token)

    refresh_token = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if refresh_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    if refresh_token.expires_at < _now():
        refresh_token.revoked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    return refresh_token


def rotate_refresh_token(db: Session, refresh_token: RefreshToken) -> str:
    new_raw_token = secrets.token_urlsafe(48)
    refresh_token.token_hash = _hash_token(new_raw_token)
    refresh_token.expires_at = _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token.revoked = False
    db.commit()
    db.refresh(refresh_token)
    return new_raw_token


def revoke_refresh_token(db: Session, refresh_token: RefreshToken) -> None:
    refresh_token.revoked = True
    db.commit()


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    return credentials.credentials


def get_current_user(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> CurrentUser:
    payload = verify_token(token)
    user_id = payload["user_id"]
    role = payload["role"]

    user = _get_user_by_role(db, user_id=user_id, role=role)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return {
        "user_id": user_id,
        "role": role,
        "user": user,
    }


def get_current_customer(
    current: CurrentUser = Depends(get_current_user),
) -> CustomerProfile:
    if current["role"] != "Customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer role required",
        )

    customer = current["user"]
    if not isinstance(customer, CustomerProfile):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return customer


def get_current_seller(
    current: CurrentUser = Depends(get_current_user),
) -> Seller:
    if current["role"] != "Seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller role required",
        )

    seller = current["user"]
    if not isinstance(seller, Seller):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return seller


def get_current_admin(
    current: CurrentUser = Depends(get_current_user),
) -> AdminProfile:
    if current["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    admin = current["user"]
    if not isinstance(admin, AdminProfile):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    return admin