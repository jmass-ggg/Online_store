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

@router.post("/login", response_model=LoginResponse)
def admin_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == form.username).first()
    if not admin:
        raise error_handler(404)

    if not verify_password(form.password, admin.hashed_password):
        raise error_handler(401)

    access = create_token({"email": admin.email})
    refresh = create_refresh_token(db, admin)

    return LoginResponse(access_token=access, refresh_token=refresh)
