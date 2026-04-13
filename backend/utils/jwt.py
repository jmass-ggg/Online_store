from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Literal, TypedDict, Union
from uuid import UUID
from fastapi import Depends, HTTPException, status
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
    email: str
    role: RoleType

class CurrentUser(TypedDict):
    email: str
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


def _now() -> datetime:
    return datetime.utcnow()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_user_by_role(db: Session, email: str, role: RoleType):
    if role == "Admin":
        return (
            db.query(AdminProfile)
            .join(AdminProfile.user)
            .options(joinedload(AdminProfile.user))
            .filter(User.email == email)
            .first()
        )

    if role == "Seller":
        return (
            db.query(Seller)
            .join(Seller.user)
            .options(joinedload(Seller.user))
            .filter(User.email == email)
            .first()
        )

    if role == "Customer":
        return (
            db.query(CustomerProfile)
            .join(CustomerProfile.user)
            .options(joinedload(CustomerProfile.user))
            .filter(User.email == email)
            .first()
        )

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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token type",
            )

        email = payload.get("sub")
        role = payload.get("role")

        if not email or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        if role not in ("Admin", "Seller", "Customer"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user role in token",
            )

        return {"email": email, "role": role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )



def create_refresh_token(db: Session, user_id: UUID, role: RoleType) -> str:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{role} not found",
        )

    return {
        "email": email,
        "role": role,
        "user": user,
    }


def get_current_customer(
    current=Depends(get_current_user),
) -> CustomerProfile:
    if current["role"] != "Customer":
        raise HTTPException(status_code=403, detail="Customer role required")

    customer = current["user"]
    if not isinstance(customer, CustomerProfile):
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


def get_current_seller(
    current=Depends(get_current_user),
) -> Seller:
    if current["role"] != "Seller":
        raise HTTPException(status_code=403, detail="Seller role required")

    seller = current["user"]
    if not isinstance(seller, Seller):
        raise HTTPException(status_code=404, detail="Seller not found")

    return seller


def get_current_admin(
    current=Depends(get_current_user),
) -> AdminProfile:
    if current["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    admin = current["user"]
    if not isinstance(admin, AdminProfile):
        raise HTTPException(status_code=404, detail="Admin not found")

    return admin