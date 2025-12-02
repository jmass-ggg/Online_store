from fastapi import APIRouter, Depends, status,Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.schemas.customer import CustomerCreate, CustomerRead, TokenResponse, CustomerUpdate,LoginResponse
from backend.utils.jwt import get_current_customer,create_refresh_token
from backend.models.customer import Customer

from backend.service.customer_service import (
    create_customer,
    customer_login,
    customer_info_update,
    delete_account_by_owner,
    # delete_account_by_admin,
    get_user
)
from backend.utils.auth import customer_schema

router=APIRouter(prefix="/user",tags=["Customer"] )

@router.post("/register",response_model=CustomerRead)
def register(user:CustomerCreate,db:Session = Depends(get_db)):
    return create_customer(db,user.username,user.email,user.password,user.phone_number,user.address)

@router.post("/login",response_model=LoginResponse)
def login(form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    return customer_login(db,form_data)

@router.patch("/update", response_model=CustomerRead)
def update_user(
    user_update: CustomerUpdate,
    current_user: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    return customer_info_update(db, user_update, current_user.id)

@router.delete("/delete",status_code=status.HTTP_200_OK)
def delete_own_account(db:Session=Depends(get_db),current_user:Customer=Depends(get_current_customer)):
    return delete_account_by_owner(db,current_user)

# @router.delete("/delete/{user_id}",status_code=status.HTTP_200_OK)
# def delete_act_by_admin(user_id:int,
#                         db:Session=Depends(get_db),
#                         current_user:Customer=Depends(get_current_user)):
    
    # return delete_account_by_admin(user_id,db,current_user)



@router.get("/me")
def get_current_user(token:str=Depends(customer_schema)):
    return get_user(token)

from backend.utils.jwt import create_token,refresh_schema,verify_refresh_token_customer
from backend.core.error_handler import error_handler

@router.post("/refresh", response_model=LoginResponse)
def refresh_token_endpoint(refresh_token: str, db: Session = Depends(get_db)):
    user = verify_refresh_token_customer(db, refresh_token)
    new_access_token = create_token({"email": user.email})
    new_refresh_token = create_refresh_token(db, user)
    return LoginResponse(access_token=new_access_token, refresh_token=new_refresh_token)
