from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from backend.database import get_db
from backend.schemas.review import Review_read, Review_create, Review_update
from backend.utils.jwt import get_current_user
from backend.models.customer import User

from backend.service.review_sevice import (
    reveiw_the_product,
    update_product_review,
    get_reviews,
    review_delete_by_customer
)


router=APIRouter(prefix="/review",tags=["Product review"])

@router.post("/{product_id}/review",response_model=Review_read)
def give_product_review(product_id:int,
                        add_review:Review_create,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(get_current_user)):
    return reveiw_the_product(product_id,add_review,db,current_user)

@router.patch("/{product_id}/change_review",response_model=Review_read)
def update_review(product_id:int,update_review:Review_update,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(get_current_user)):
    return update_product_review(product_id,update_review,db,current_user)

@router.delete("/{review_id}/delete",status_code=status.HTTP_200_OK)
def delete_review(review_id:int,
                  db:Session=Depends(get_db)
                  ,current_user:User=Depends(get_current_user)):
    return review_delete_by_customer(review_id,db,current_user)

@router.get("/{product_id}/change_review",response_model=Review_read)
def get_review(product_id:int,
                        db:Session=Depends(get_db),
                        current_user:User=Depends(get_current_user)):
    return get_reviews(product_id,db,current_user)