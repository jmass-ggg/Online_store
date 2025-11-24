from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.customer import Customer
from backend.models.seller import Seller
from backend.utils.auth import auth2_schema
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

def create_refresh_token():
    token = secrets.token_hex(40)
    expire = datetime.utcnow() + timedelta(days=30)
    return token, expire

def verify_refresh_token(refresh_token: str, db: Session):
    token_obj = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.revoked == False
    ).first()
    if not token_obj or token_obj.expires_at < datetime.utcnow():
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    return token_obj

def get_customer_from_refresh(
    refresh_token: str = Depends(auth2_schema),
    db: Session = Depends(get_db)
) -> Customer:
    refresh = verify_refresh_token(refresh_token, db)

    user = db.query(Customer).filter(Customer.id == refresh.user_id).first()
    if not user:
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "User not found")

    return user
def get_seller_from_refresh(
    refresh_token: str = Depends(auth2_schema),
    db: Session = Depends(get_db)
) -> Seller:
    refresh = verify_refresh_token(refresh_token, db)

    seller = db.query(Seller).filter(Seller.id == refresh.user_id).first()
    if not seller:
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "User not found")

    return seller