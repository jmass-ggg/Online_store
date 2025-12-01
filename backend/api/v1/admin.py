from fastapi import APIRouter, Depends, status,Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.schemas.admin import AdminLogin,LoginResponse
from backend.utils.jwt import get_current_customer,create_refresh_token
from backend.models.admin import Admin
from backend.service.admin_service import(
    admin_login
)


router=APIRouter(prefix="/admin",tags="Admin Authanization")

@router.post("/login",response_model=LoginResponse)
def login_admin(form_data: OAuth2PasswordRequestForm,db: Session):
    return admin_login(db,form_data)