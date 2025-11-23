from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from backend.database import get_db
from backend.models.admin import Admin
from backend.models.role import Roles
from backend.schemas.customer import (
    TokenResponse
)
from backend.utils.jwt import create_token, verify_token
from backend.utils.hashed import  verify_password
from backend.utils.hashed import hashed_password as hashed_pwd
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler

def admin_login(db: Session, form_data: OAuth2PasswordRequestForm)->TokenResponse:
    admin=db.query(Admin).filter(Admin.email == form_data.username).first()
    if not admin:
        raise error_handler(status.HTTP_401_UNAUTHORIZED,"Imvalid creditions")
    token