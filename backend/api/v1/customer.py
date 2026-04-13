from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.database import get_db
from backend.models.customer import CustomerProfile
from backend.schemas.customer import (
    CustomerRegisterRequest,
    CustomerProfileResponse,
    CustomerUpdate,
)
from backend.service.customer_service import (
    register_customer,
    customer_info_update,
    delete_account_by_owner,
    verify_user_email,
)
from backend.utils.jwt import get_current_customer

router = APIRouter(prefix="/user", tags=["Customer"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=CustomerProfileResponse)
def register(
    request: Request,
    background_tasks: BackgroundTasks,
    user: CustomerRegisterRequest,
    db: Session = Depends(get_db),
):
    return register_customer(db, user, background_tasks)


@router.get("/verified-email", status_code=status.HTTP_200_OK)
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    return verify_user_email(token, db)


@router.patch("/update", response_model=CustomerProfileResponse)
def update_user(
    user_update: CustomerUpdate,
    current_user: CustomerProfile = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    return customer_info_update(db, user_update, current_user.user_id)


@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_own_account(
    db: Session = Depends(get_db),
    current_user: CustomerProfile = Depends(get_current_customer),
):
    return delete_account_by_owner(db, current_user.user_id)


@router.get("/me", response_model=CustomerProfileResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user: CustomerProfile = Depends(get_current_customer),
):
    return (
        db.query(CustomerProfile)
        .options(joinedload(CustomerProfile.user))
        .filter(CustomerProfile.id == current_user.id)
        .first()
    )