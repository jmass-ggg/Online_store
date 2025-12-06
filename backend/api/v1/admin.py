from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.utils.jwt import create_token, create_refresh_token
from backend.models.admin import Admin
from backend.utils.hashed import verify_password
from backend.schemas.admin import LoginResponse
from backend.core.error_handler import error_handler
router = APIRouter(prefix="/admin", tags=["Admin Authentication"])


