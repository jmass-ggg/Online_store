from fastapi import APIRouter, Depends, HTTPException, status, UploadFile,Query
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError
from backend.database import get_db
from backend.utils.verifyied import verify_seller_or_not
from backend.models.product import Product,ProductStatus,ProductCategory
from backend.models.seller import Seller
from backend.models.product_img import ProductImage
from backend.models.ProductVariant import ProductVariant
from backend.schemas.product import ProductCreate,ProductRead,ProductUpdate,ProductVariantCreate,ProductVariantRead,AllProduct,ProductImageBase,ProductImageRead,ProductImageUpdate
from backend.core.sku import  generate_hybrid_sku
from backend.core.permission import check_permission
from backend.core.error_handler import error_handler
from backend.models.admin import Admin
from sqlalchemy import or_, func
from typing import Optional
from backend.core.random_slang_url import generate_unique_url_slug
from datetime import datetime
from uuid import uuid4
from backend.core.settings import UPLOAD_DIR

UPLOAD_FOLDER="backend/uploads/"

def add_product_by_seller(
    product_name: str,
    product_category: ProductCategory,
    description: str | None,
    image: UploadFile,
    db: Session,
    current_seller: Seller,
    upload_folder: str,
) -> ProductRead:

    os.makedirs(upload_folder, exist_ok=True)

    filename = image.filename
    file_path = os.path.join(upload_folder, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    url_slug = generate_unique_url_slug(db, product_name)

    new_product = Product(
        product_name=product_name,
        url_slug=url_slug,
        product_category=product_category,
        description=description,
        image_url=f"/uploads/{filename}",
        status=ProductStatus.inactive,
        seller_id=current_seller.id,
    )

    db.add(new_product)
    db.flush()  
    db.commit()
    db.refresh(new_product)

    return ProductRead.from_orm(new_product)

def upload_single_product_image(
    product_id: int,
    image: UploadFile = File(...),
    is_primary: bool = False,
    sort_order: int = 0,db: Session=Depends(get_db),current_seller:Session=Decimal(verify_seller_or_not)):
    try:
        product=db.query(Product).filter(Product.id == product_id).one_or_none()
        if not product:
            raise error_handler(403,"Product not Found")
        os.makedirs(UPLOAD_FOLDER)
        ext = os.path.splitext(image.filename)[1].lower()
        filename = f"{uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        with db.begin(): 
            if is_primary:
                db.query(ProductImage).filter(
                    ProductImage.product_id == product_id,
                    ProductImage.is_primary == True
                ).update({"is_primary": False})

            row = ProductImage(
                product_id=product_id,
                image_url=f"/uploads/{filename}",
                is_primary=is_primary,
                sort_order=sort_order,
            )
            db.add(row)
            db.flush() 

        db.refresh(row)
        return ProductImageRead.from_orm(row)
    except SQLAlchemyError:
        db.rollback()
        raise error_handler(500,"Failed to save product image")

def upload_multiple_product_images(
    product_id: int,
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    product = db.query(Product).filter(Product.id == product_id).one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.seller_id != current_seller.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    saved_rows: list[ProductImage] = []

    try:
        with db.begin():  
            last_sort = (
                db.query(ProductImage.sort_order)
                .filter(ProductImage.product_id == product_id)
                .order_by(ProductImage.sort_order.desc())
                .first()
            )
            start_sort = (last_sort[0] + 1) if last_sort else 0

            for i, img in enumerate(images):
                ext = os.path.splitext(img.filename)[1].lower()
                filename = f"{uuid4().hex}{ext}"
                file_path = os.path.join(UPLOAD_DIR, filename)

               
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(img.file, f)

               
                row = ProductImage(
                    product_id=product_id,
                    image_url=f"/uploads/{filename}",
                    is_primary=False,
                    sort_order=start_sort + i,
                )
                db.add(row)
                saved_rows.append(row)

            db.flush() 


        for r in saved_rows:
            db.refresh(r)

        return [ProductImageRead.from_orm(r) for r in saved_rows]

    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload product images")
    
def add_product_variant(
    db: Session,
    product_id: int,
    variants: list[ProductVariantCreate],
    current_seller: Seller,
) -> list[ProductVariant]:

    product = db.query(Product).filter(Product.id == product_id).one_or_none()

    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    if product.seller_id != current_seller.id:
        raise error_handler(status.HTTP_403_FORBIDDEN, "Not authorized")

    created_variants: list[ProductVariant] = []
    sku = generate_hybrid_sku(db, product.url_slug, v.color, v.size)
    for v in variants:
        variant = ProductVariant(
            product_id=product.id,
            sku=sku,
            color=v.color,
            size=v.size,
            price=v.price,
            stock_quantity=v.stock_quantity,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(variant)
        created_variants.append(variant)

    product.status = ProductStatus.active
    db.commit()  

    return created_variants

def view_product(db: Session, product_id: int) -> AllProduct:
    product = db.query(Product).filter(Product.id == product_id).one_or_none()

    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")
    return ProductRead.from_orm(product)

def view_product_by_slug(db: Session, slug: str) -> ProductRead:
    product = db.query(Product).filter(Product.url_slug == slug).one_or_none()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")
    return ProductRead.from_orm(product)

def search_products(
    *,
    q: str,
    category: Optional[ProductCategory],
    skip: int,
    limit: int,
    db: Session,
) -> List[ProductRead]:
    term = q.strip()
    if not term:
        return []

    like = f"%{term.lower()}%"
    active_value = getattr(ProductStatus.active, "value", ProductStatus.active)

    query = (
        db.query(Product)
        .filter(Product.status == active_value)
    )

    if category is not None:
        query = query.filter(Product.product_category == category)

    query = query.filter(
        or_(
            func.lower(func.trim(Product.product_name)).like(like),
            func.lower(func.trim(Product.url_slug)).like(like),
            func.lower(func.trim(Product.description)).like(like),
        )
    ).order_by(Product.created_at.desc())

    products = query.offset(skip).limit(limit).all()
    return [ProductRead.from_orm(p) for p in products]

def view_all_product(
    db: Session,
    category: Optional[ProductCategory] = None,
    skip: int = 0,
    limit: int = 20,
    only_active: bool = True,
):
    query = db.query(Product)

    if only_active:
        query = query.filter(Product.status == ProductStatus.active)

    if category:
        query = query.filter(Product.product_category == category)

    products = (
        query.order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [ProductRead.from_orm(p) for p in products]


def edit_product_by_seller(
    db: Session,
    product_id: int,
    product_update: ProductUpdate,
    current_seller: Seller,
) -> ProductRead:

    product = db.query(Product).filter(Product.id == product_id).one_or_none()

    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    if product.seller_id != current_seller.id:
        raise error_handler(status.HTTP_403_FORBIDDEN, "Not authorized")

    for key, value in product_update.dict(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return ProductRead.from_orm(product)


def delete_product_by_admin(
    db: Session,
    product_id: int,
    current_admin: Admin,
) -> dict:

    if current_admin.role != "Admin":
        raise error_handler(status.HTTP_403_FORBIDDEN, "Admin only")

    product = db.query(Product).filter(Product.id == product_id).one_or_none()

    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}

def delete_product_by_seller(
    db: Session,
    product_id: int,
    current_seller: Seller,
) -> dict:

    product = db.query(Product).filter(Product.id == product_id).one_or_none()

    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    if product.seller_id != current_seller.id:
        raise error_handler(status.HTTP_403_FORBIDDEN, "Not authorized")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}



def view_all_product_seller(seller_id: int, db: Session) -> List[ProductRead]:
    products = (
        db.query(Product)
        .filter(Product.seller_id == seller_id)
        .order_by(Product.created_at.desc())
        .all()
    )
    return [ProductRead.from_orm(p) for p in products]
