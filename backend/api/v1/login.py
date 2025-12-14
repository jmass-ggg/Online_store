from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from backend.database import get_db
from backend.utils.jwt import create_token, create_refresh_token
from backend.utils.hashed import verify_password
from backend.core.error_handler import error_handler

from backend.models.admin import Admin
from backend.models.seller import Seller
from backend.models.customer import Customer

from backend.schemas.customer import LoginResponse

router = APIRouter(prefix="/login", tags=["Login"])


@router.post("/", response_model=LoginResponse)
def unified_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):

    email = form_data.username
    password = form_data.password

    # 1. Check ADMIN
    admin = db.query(Admin).filter(Admin.email == email).first()
    if admin:
        if not verify_password(password, admin.hashed_password):
            raise error_handler(401, "Invalid password")
        access = create_token(email=admin.email, role="Admin")
        refresh = create_refresh_token(db, admin)
        return LoginResponse(access_token=access, refresh_token=refresh)

    # 2. Check SELLER
    seller = db.query(Seller).filter(Seller.email == email).first()
    if seller:
        if not verify_password(password, seller.hashed_password):
            raise error_handler(401, "Invalid password")
        access = create_token(email=seller.email, role="Seller")
        refresh = create_refresh_token(db, seller)
        return LoginResponse(access_token=access, refresh_token=refresh)

    # 3. Check CUSTOMER
    customer = db.query(Customer).filter(Customer.email == email).first()
    if customer:
        if not verify_password(password, customer.hashed_password):
            raise error_handler(401, "Invalid password")
        access = create_token(email=customer.email, role="Customer")
        refresh = create_refresh_token(db, customer)
        return LoginResponse(access_token=access, refresh_token=refresh)

    # No user found
    raise error_handler(404, "User not found")
