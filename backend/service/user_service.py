from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.utils.jwt import create_access_token, verify_token, create_refresh_token
from backend.utils.hashed import verify_password
from backend.models.role import Role
from backend.models.user import User
from backend.schemas.user import UserRegisterRequest, UserRegisterResponse
from backend.utils.hashed import hashed_password 

def ensure_user_not_exists(db:Session,username:str,email:str):
    existing_user=db.query(User).filter(
        User.email == email,User.username == username
    ).first()
    if not existing_user:
        return

    if existing_user.username == username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )

    if existing_user.email == email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists.",
        )
    
    
    
def create_user_instance(
    db: Session,
    *,
    username: str,
    email: str,
    password: str,
    account_status: str = "ACTIVE",
) -> User:
    ensure_user_not_exists(db, username=username, email=email)

    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password(password),
        account_status=account_status,
        is_email_verified=False,
    )
    db.add(user)
    db.flush()
    return user