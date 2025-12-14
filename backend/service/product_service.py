from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from typing import List
import os
import shutil

from backend.database import get_db
from backend.models.product import Product
from backend.models.seller import Seller
from backend.schemas.product import Product_create, Product_read, Product_update
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler

def add_product_by_seller(
    product_name: str,
    product_category: str,
    stock: str,
    price: float,
    description: str,
    image: UploadFile,
    db: Session,
    current_user: Seller,
    UPLOAD_FOLDER: str
) -> Product_create:
    """
    Allow a seller to add a new product with image upload.
    """
    if not check_permission(current_user, "add_product"):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized action")

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_location = os.path.join(UPLOAD_FOLDER, image.filename)

    with open(file_location, "wb") as f:
        shutil.copyfileobj(image.file, f)

    image_url = f"/uploads/{image.filename}"

    new_product = Product(
        product_name=product_name,
        product_category=product_category,
        stock=stock,
        price=price,
        description=description,
        image_url=image_url,
        seller_id=current_user.id
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return Product_read.from_orm(new_product)

def edit_product_by_seller(
    db: Session,
    product_id: int,
    product_update: Product_update,
    current_user: Seller
) -> Product_update:
    """
    Edit a product by seller. Sellers can edit their own products or admins can edit any.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    can_edit_any = check_permission(current_user, "edit_any_product")
    can_edit_own = check_permission(current_user, "edit_own_product") and product.seller_id == current_user.id

    if not (can_edit_any or can_edit_own):
        raise error_handler(status.HTTP_401_UNAUTHORIZED, "Unauthorized action")

    update_data = product_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return Product_update.from_orm(product)

def delete_product_by_admin(
    db: Session,
    product_id: int,
) -> dict:
    """
    Allow admin to delete any product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    db.delete(product)
    db.commit()

    return {"message": f"Product '{product.product_name}' has been removed by admin"}

def delete_product_by_seller(
    db: Session,
    product_id: int
) -> dict:
    """
    Allow seller to delete their own product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    db.delete(product)
    db.commit()

    return {"message": f"Product '{product.product_name}' has been removed from the list"}

def veiw_product(
    db: Session,
    product_id: int,
    
) -> Product_read:
    """
    Retrieve details of a single product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    return Product_read.from_orm(product)

def view_all_product(
    db: Session
) -> List[Product_read]:
    """
    Retrieve all products.
    """
    products = db.query(Product).all()
    return [Product_read.from_orm(p) for p in products]
