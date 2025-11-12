from fastapi import APIRouter, Depends, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.schemas.product import Product_create, Product_read, Product_update
from backend.models.customer import User
from backend.utils.jwt import get_current_user
from backend.core.permission import require_permission
from backend.service.product_service import (
    add_product_by_seller,
    edit_product_by_seller,
    delete_product_by_admin,
    delete_product_by_seller,
    veiw_product,
    view_all_product
)


UPLOAD_FOLDER="backend/uploads/"
router=APIRouter(prefix="/product",tags=["Product"])

@router.post("/adding_product", response_model=Product_read)
def product_add(
    product_name: str = Form(...),
    product_category: str = Form(...),
    stock: int = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("add_product"))
):
    return add_product_by_seller(product_name,product_category,stock,price,description,image,db,current_user,UPLOAD_FOLDER)

@router.patch("/{product_id}", response_model=Product_read)
def product_edit(
    product_id: int,
    product_update: Product_update,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    return edit_product_by_seller(db,product_id,product_update,current_user)

@router.delete("/{product_id}/admin",status_code=status.HTTP_200_OK)
def delete_product(product_id:int,db:Session=Depends(get_db),
                current_user:User=Depends(require_permission("delete_any_product"))):
    return delete_product_by_admin(db,product_id,current_user)

@router.delete("/{product_id}/seller",status_code=status.HTTP_200_OK)
def delete_product(product_id:int,db:Session=Depends(get_db),
                current_user:User=Depends(require_permission("delete_own_product"))):
    return delete_product_by_seller(db,product_id)

@router.get("/{product_id}",response_model=Product_read)
def get_product(product_id:int,db:Session=Depends(get_db),
                current_user:User=Depends(require_permission("view_own_orders"))):
    return veiw_product(db,product_id,current_user)

@router.get("/",response_model=List[Product_read])
def get_all_product(db:Session=Depends(get_db)
                    ,current_user:User=Depends(require_permission("view_own_orders"))):
    return view_all_product(db)