from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.customer import Customer
from backend.models.admin import Admin
from backend.models.seller import Seller
from backend.utils.auth import (
    customer_schema,admin_schema,seller_schema,refresh_schema
)

from backend.core.error_handler import error_handler
from pydantic import BaseSettings
import secrets
from backend.models.refresh_token import RefreshToken
class Settings(BaseSettings):
    SECRET_KEY : str
    ALGORITHM : str
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 30 

    class Config:
        env_file=".env"
        
settings=Settings()

def create_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update(
        {
            "sub":str(data.get("email")),
            "exp":expire
        }
    )
    return jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)

def verify_token(Token:str):
    try:
        payload = jwt.decode(Token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_email=payload.get("sub")
        if not user_email:
            raise error_handler(status.HTTP_401_UNAUTHORIZED, "Invalid token")
        return user_email 
    except JWTError:
        raise error_handler(status.HTTP_401_UNAUTHORIZED,"Invalid or expired token")


import secrets

REFRESH_TOKEN_EXPIRE_DAYS = 7  

def create_refresh_token(db: Session, user) -> str:
    token = secrets.token_urlsafe(32)  # secure random token
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = RefreshToken(
        token=token,
        user_id=user.id,
        expires_at=expires_at
    )

    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return token

def verify_refresh_token_customer(db: Session, token: str) -> Customer:
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if not refresh_token:
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    if refresh_token.expires_at < datetime.utcnow():
        db.delete(refresh_token)
        db.commit()
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    return refresh_token.user_id
def verify_refresh_token_seller(db: Session, token: str) -> Seller:
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if not refresh_token:
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    if refresh_token.expires_at < datetime.utcnow():
        db.delete(refresh_token)
        db.commit()
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    return refresh_token.user_id

def get_current_customer(
    token: str = Depends(customer_schema),
    db: Session = Depends(get_db)
):
    email = verify_token(token)
    user = db.query(Customer).filter(Customer.email == email).first()
    if not user:
        raise error_handler(404, "Customer not found")
    return user


def get_current_seller(
    token: str = Depends(seller_schema),
    db: Session = Depends(get_db)
):
    email = verify_token(token)
    user = db.query(Seller).filter(Seller.email == email).first()
    if not user:
        raise error_handler(404, "Seller not found")
    return user


def get_current_admin(token: str = Depends(admin_schema),
    db: Session = Depends(get_db)):
    email = verify_token(token)
    user = db.query(Admin).filter(Admin.email == email).first()
    if not user:
        raise error_handler(401, "Admin not found")
    return user
