from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from backend.database import get_db
from backend.models.product import Product,ProductStatus,ProductCategory
from backend.models.seller import Seller
from backend.models.ProductVariant import ProductVariant
from backend.schemas.product import ProductCreate,ProductRead,ProductUpdate,ProductVariantCreate
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler

def add_product_by_seller(
    product_name: str,
    url_slug:str,
    product_category: str,
    description: str,
    image_url: UploadFile,
    db: Session,
    current_seller: Seller,
    UPLOAD_FOLDER: str,
) -> ProductCreate:
    """
    Allow a seller to add a new product with image upload.
    """
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_location = os.path.join(UPLOAD_FOLDER, image_url.filename)

        with open(file_location, "wb") as f:
            shutil.copyfileobj(image_url.file, f)

        image_url = f"/uploads/{image_url.filename}"

        new_product = Product(
            product_name=product_name,
            url_slug=url_slug,
            product_category=product_category,
            description=description,
            image_url=image_url,
            status=ProductStatus.inactive,
            seller_id=current_seller.id
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return ProductRead.from_orm(new_product)
    except SQLAlchemyError:
        raise error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR," ")
    
def add_product_variant(
    db: Session,
    product_id: int,
    variants: list[ProductVariantCreate],
    current_seller: Seller,
)->list[ProductVariant]:
    try:
        product=db.query(Seller).filter(Product.id == product_id).one_or_none()
        
        if not product:
            raise error_handler(status.HTTP_404_NOT_FOUND,"product not found")
        create_variants:list[ProductVariant]=[]
        with db.begin():
            for v in variants:
                new_variants=ProductVariant(
                    product_id=product.id,
                    color=v.color,
                    size=v.size,
                    price=v.price,
                    stock_quantity=v.stock_quantity,
                )
                db.add(new_variants)
                create_variants.append(new_variants)
            product.status=ProductStatus.active
        return create_variants
    except SQLAlchemyError:
        db.rollback()
        raise error_handler(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to add variants",
        ) 


def edit_product_by_seller(
    db: Session,
    product_id: int,
    product_update: ProductUpdate,
    current_seller: Seller
) -> ProductUpdate:
    """
    Edit a product by seller. Sellers can edit their own products or admins can edit any.
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).one_or_none()
        if not product:
            raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

        update_data = product_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(product, key, value)
        db.commit()
        db.refresh(product)
        return ProductUpdate.from_orm(product)
    except SQLAlchemyError:
        db.rollback()
        raise error_handler(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to add variants",
        )

def delete_product_by_admin(
    db: Session,
    product_id: int,
    currrent_admin
) -> dict:
    """
    Allow admin to delete any product.
    """
    
    product = db.query(Product).filter(Product.id == product_id).one_or_none()
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
    product = db.query(Product).filter(Product.id == product_id).one_or_none()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    db.delete(product)
    db.commit()

    return {"message": f"Product '{product.product_name}' has been removed from the list"}

def veiw_product(
    db: Session,
    product_id: int,current_user
    
) -> ProductRead:
    """
    Retrieve details of a single product.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    return ProductRead.from_orm(product)

def view_all_product(
    db: Session,
    skip:0,
    limit:20
) -> List[ProductRead]:
    """
    Retrieve all products.
    """
    products = db.query(Product).offset(skip).limit(limit).all()
    return [ProductRead.from_orm(product) for product in products]
