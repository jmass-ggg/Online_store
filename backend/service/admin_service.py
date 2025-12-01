# backend/service/admin_service.py
from fastapi import status
from sqlalchemy.orm import Session

from backend.models.admin import Admin
from backend.schemas.admin import LoginResponse
from backend.utils.jwt import create_token, create_refresh_token
from backend.utils.hashed import verify_password
from backend.core.error_handler import error_handler

def admin_login(db: Session, form_data) -> LoginResponse:
    admin = db.query(Admin).filter(Admin.email == form_data.username).first()

    if not admin:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Admin not found")

    if not verify_password(form_data.password, admin.hashed_password):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    access_token = create_token({"email": admin.email})
    refresh_token = create_refresh_token(db, admin)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )
