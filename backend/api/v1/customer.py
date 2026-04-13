from fastapi import APIRouter, Depends, status,Form,Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.utils.jwt import get_current_customer,create_refresh_token
from backend.models.customer import CustomerProfile
from backend.service.customer_service import register_customer,customer_info_update,delete_account_by_owner,get_user
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.schemas.customer import CustomerRegisterRequest,CustomerProfileResponse,CustomerUpdate


router=APIRouter(prefix="/user",tags=["Customer"] )
limiter=Limiter(key_func=get_remote_address)

# @limiter.limit("5/minute")
@router.post("/register",response_model=CustomerProfileResponse)
def register(request:Request,user:CustomerRegisterRequest,db:Session = Depends(get_db)):
    return register_customer(db,user)



@router.patch("/update", response_model=CustomerProfileResponse)
def update_user(
    user_update: CustomerUpdate,
    current_user: CustomerProfile = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    return customer_info_update(db, user_update, current_user.id)


@router.delete("/delete",status_code=status.HTTP_200_OK)
def delete_own_account(db:Session=Depends(get_db),current_user:CustomerProfile=Depends(get_current_customer)):
    return delete_account_by_owner(db,current_user.id)

# @router.delete("/delete/{user_id}",status_code=status.HTTP_200_OK)
# def delete_act_by_admin(user_id:int,
#                         db:Session=Depends(get_db),
#                         current_user:Customer=Depends(get_current_user)):
    
    # return delete_account_by_admin(user_id,db,current_user)

