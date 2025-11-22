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
#Get current user
def get_current_user(token:str=Depends(auth2_schema),db:Session=Depends(get_db)):
    email=verify_token(token)
    user=db.query(Customer).filter(Customer.email == email).first()
    if not user:
        raise error_handler(status.HTTP_401_UNAUTHORIZED,"Customer not found")
    return user
# Get current seller
def get_current_seller(token:str=Depends(auth2_schema),db:Session=Depends(get_db)):
    email=verify_token(token)
    seller=db.query(Seller).filter(Seller.email == email).first()
    if not seller:
        raise error_handler(status.HTTP_401_UNAUTHORIZED,"Customer not found")
    return seller