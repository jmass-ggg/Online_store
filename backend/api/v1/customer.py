from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.schemas.customer import CustomerCreate, CustomerRead, TokenResponse, CustomerUpdate
from backend.utils.jwt import get_current_user
from backend.models.customer import User
from backend.service.customer_service import (
    create_customer,
    customer_login,
    customer_info_update,
    delete_account_by_owner,
    delete_account_by_admin,
    get_user
)
from backend.utils.auth import auth2_schema

router=APIRouter(prefix="/user",tags=["Authentication"] )

@router.post("/register",response_model=CustomerRead)
def register(user:CustomerCreate,db:Session = Depends(get_db)):
    return create_customer(db,user.username,user.email,user.password,user.phone_number)

@router.post("/login",response_model=TokenResponse)
def login(form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    return customer_login(db,form_data)

@router.patch("/{user_id}/update",response_model=CustomerRead)
def update_user(user_id:int,user_update:CustomerUpdate,
                db:Session=Depends(get_db),
                current_user:User=Depends(get_current_user)):
    return customer_info_update(db,user_id,user_update)

@router.delete("/delete",status_code=status.HTTP_200_OK)
def delete_own_account(db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):
    return delete_account_by_owner(db,current_user)

@router.delete("/delete/{user_id}",status_code=status.HTTP_200_OK)
def delete_act_by_admin(user_id:int,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(get_current_user)):
    
    return delete_account_by_admin(user_id,db,current_user)

@router.get("/me")
def get_current_user(token:str=Depends(auth2_schema)):
    return get_user(token)