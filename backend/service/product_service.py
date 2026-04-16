from __future__ import annotations

import os
import shutil
from uuid import UUID, uuid4
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, aliased, joinedload, selectinload

from backend.core.error_handler import error_handler
from backend.core.random_slang_url import generate_unique_url_slug
from backend.core.settings import UPLOAD_DIR
from backend.core.sku import generate_hybrid_sku
from backend.models.admin import AdminProfile
from backend.models.product import Product, ProductCategory, ProductStatus, TargetAudience
from backend.models.product_img import ProductImage
from backend.models.product_variant import ProductVariant
from backend.models.seller import Seller
from backend.schemas.product import (
    AllProduct,
    ProductImageRead,
    ProductImageUpdate,
    ProductRead,
    ProductUpdate,
    ProductVariantCreate,ProductVariantRead
)


def _get_product_or_404(db: Session, product_id: UUID) -> Product:
    product = (
        db.query(Product)
        .options(
            joinedload(Product.seller),
            selectinload(Product.images),
            selectinload(Product.variants),
        )
        .filter(Product.id == product_id)
        .one_or_none()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _ensure_product_owner(product: Product, current_seller: Seller) -> None:
    if product.seller_id != current_seller.id:
        raise HTTPException(status_code=403, detail="Not authorized")


def _save_upload_file(image: UploadFile) -> tuple[str, str]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = os.path.splitext(image.filename or "")[1].lower()
    filename = f"{uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    return filename, file_path


def _next_sort_order(db: Session, product_id: UUID) -> int:
    last_sort = (
        db.query(func.max(ProductImage.sort_order))
        .filter(ProductImage.product_id == product_id)
        .scalar()
    )
    return 0 if last_sort is None else int(last_sort) + 1


def _unset_existing_primary(db: Session, product_id: UUID) -> None:
    (
        db.query(ProductImage)
        .filter(
            ProductImage.product_id == product_id,
            ProductImage.is_primary.is_(True),
        )
        .update({"is_primary": False}, synchronize_session=False)
    )


def add_product_by_seller(
    *,
    product_name: str,
    target_audience: TargetAudience,
    product_category: ProductCategory,
    description: str | None,
    db: Session,
    current_seller: Seller,
) -> ProductRead:
    url_slug = generate_unique_url_slug(db, product_name)

    new_product = Product(
        product_name=product_name,
        url_slug=url_slug,
        target_audience=target_audience,
        product_category=product_category,
        description=description,
        status=ProductStatus.INACTIVE,
        seller_id=current_seller.id,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return ProductRead.model_validate(new_product)


def upload_single_product_image(
    *,
    product_id: UUID,
    image: UploadFile,
    db: Session,
    current_seller: Seller,
    color: str | None = None,
    is_primary: bool | None = None,
    sort_order: int | None = None,
) -> ProductImageRead:
    product = _get_product_or_404(db, product_id)
    _ensure_product_owner(product, current_seller)

    existing_primary = (
        db.query(ProductImage)
        .filter(
            ProductImage.product_id == product_id,
            ProductImage.is_primary.is_(True),
        )
        .first()
    )

    make_primary = is_primary if is_primary is not None else existing_primary is None
    sort_value = sort_order if sort_order is not None else _next_sort_order(db, product_id)

    filename, saved_path = _save_upload_file(image)

    try:
        if make_primary:
            _unset_existing_primary(db, product_id)

        row = ProductImage(
            product_id=product_id,
            color=color,
            image_url=f"/uploads/{filename}",
            is_primary=make_primary,
            sort_order=sort_value,
        )
        db.add(row)
        db.commit()
        db.refresh(row)

        return ProductImageRead.model_validate(row)

    except IntegrityError:
        db.rollback()
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=400, detail="Only one primary image and unique sort_order are allowed per product")

    except SQLAlchemyError:
        db.rollback()
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail="Failed to save product image")


def upload_multiple_product_images(
    *,
    product_id: UUID,
    images: list[UploadFile],
    db: Session,
    current_seller: Seller,
    color: str | None = None,
    primary_index: int | None = None,
) -> list[ProductImageRead]:
    if not images:
        raise HTTPException(status_code=400, detail="Please upload at least one image")

    product = _get_product_or_404(db, product_id)
    _ensure_product_owner(product, current_seller)

    existing_primary = (
        db.query(ProductImage)
        .filter(
            ProductImage.product_id == product_id,
            ProductImage.is_primary.is_(True),
        )
        .first()
    )

    if primary_index is not None and (primary_index < 0 or primary_index >= len(images)):
        raise HTTPException(status_code=400, detail="primary_index is out of range")

    chosen_primary_index = primary_index
    if existing_primary is None and chosen_primary_index is None:
        chosen_primary_index = 0

    start_sort = _next_sort_order(db, product_id)
    saved_files: list[str] = []
    saved_rows: list[ProductImage] = []

    try:
        if chosen_primary_index is not None:
            _unset_existing_primary(db, product_id)

        for i, img in enumerate(images):
            filename, file_path = _save_upload_file(img)
            saved_files.append(file_path)

            row = ProductImage(
                product_id=product_id,
                color=color,
                image_url=f"/uploads/{filename}",
                is_primary=(i == chosen_primary_index),
                sort_order=start_sort + i,
            )
            db.add(row)
            saved_rows.append(row)

        db.commit()

        for row in saved_rows:
            db.refresh(row)

        return [ProductImageRead.model_validate(row) for row in saved_rows]

    except IntegrityError:
        db.rollback()
        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        raise HTTPException(status_code=400, detail="Only one primary image and unique sort_order are allowed per product")

    except SQLAlchemyError:
        db.rollback()
        for file_path in saved_files:
            if os.path.exists(file_path):
                os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to upload product images")


def update_product_image(
    *,
    image_id: UUID,
    data: ProductImageUpdate,
    db: Session,
    current_seller: Seller,
) -> ProductImageRead:
    image = (
        db.query(ProductImage)
        .join(Product, Product.id == ProductImage.product_id)
        .filter(ProductImage.id == image_id)
        .one_or_none()
    )
    if not image:
        raise HTTPException(status_code=404, detail="Product image not found")

    product = _get_product_or_404(db, image.product_id)
    _ensure_product_owner(product, current_seller)

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_primary") is True:
        _unset_existing_primary(db, image.product_id)

    if update_data.get("is_primary") is False:
        other_primary = (
            db.query(ProductImage)
            .filter(
                ProductImage.product_id == image.product_id,
                ProductImage.id != image.id,
                ProductImage.is_primary.is_(True),
            )
            .first()
        )
        if not other_primary:
            raise HTTPException(status_code=400, detail="A product must have at least one primary image")

    for key, value in update_data.items():
        setattr(image, key, value)

    try:
        db.commit()
        db.refresh(image)
        return ProductImageRead.model_validate(image)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Only one primary image and unique sort_order are allowed per product")


def add_product_variant(
    *,
    db: Session,
    product_id: UUID,
    variants: list[ProductVariantCreate],
    current_seller: Seller,
) -> list[ProductVariant]:
    product = _get_product_or_404(db, product_id)
    _ensure_product_owner(product, current_seller)

    seen_combinations: set[tuple[str | None, str | None]] = set()
    created_variants: list[ProductVariant] = []

    try:
        for v in variants:
            key = (v.color, v.size)
            if key in seen_combinations:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate variant in request: color={v.color}, size={v.size}",
                )
            seen_combinations.add(key)

            exists = (
                db.query(ProductVariant.id)
                .filter(
                    ProductVariant.product_id == product_id,
                    ProductVariant.color == v.color,
                    ProductVariant.size == v.size,
                )
                .first()
            )
            if exists:
                raise HTTPException(
                    status_code=400,
                    detail=f"Variant already exists: color={v.color}, size={v.size}",
                )

            sku = generate_hybrid_sku(db, product.url_slug, v.color, v.size)

            variant = ProductVariant(
                product_id=product_id,
                sku=sku,
                color=v.color,
                size=v.size,
                price=v.price,
                stock_quantity=v.stock_quantity,
                is_active=(v.stock_quantity > 0),
            )
            db.add(variant)
            created_variants.append(variant)

        if created_variants:
            product.status = ProductStatus.ACTIVE

        db.commit()

        for variant in created_variants:
            db.refresh(variant)

        return created_variants

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate variant detected")

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error while creating variants")
    
    
def view_product(db: Session, product_id: UUID) -> AllProduct:
    product = (
        db.query(Product)
        .options(selectinload(Product.variants), selectinload(Product.images))
        .filter(Product.id == product_id, Product.status == ProductStatus.ACTIVE)
        .one_or_none()
    )
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")
    return AllProduct.model_validate(product)


def view_product_by_slug(db: Session, slug: str) -> AllProduct:
    product = (
        db.query(Product)
        .options(selectinload(Product.variants), selectinload(Product.images))
        .filter(Product.url_slug == slug, Product.status == ProductStatus.ACTIVE)
        .one_or_none()
    )
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")
    return AllProduct.model_validate(product)


def search_products(
    *,
    q: str,
    category: Optional[ProductCategory],
    skip: int,
    limit: int,
    db: Session,
) -> list[ProductRead]:
    term = q.strip()
    if not term:
        return []

    like = f"%{term.lower()}%"

    query = db.query(Product).filter(Product.status == ProductStatus.ACTIVE)

    if category is not None:
        query = query.filter(Product.product_category == category)

    query = query.filter(
        or_(
            func.lower(func.trim(Product.product_name)).like(like),
            func.lower(func.trim(Product.url_slug)).like(like),
            func.lower(func.trim(func.coalesce(Product.description, ""))).like(like),
        )
    ).order_by(Product.created_at.desc())

    products = query.offset(skip).limit(limit).all()
    return [ProductRead.model_validate(product) for product in products]


def view_all_product(
    *,
    db: Session,
    category: Optional[ProductCategory] = None,
    skip: int = 0,
    limit: int = 20,
    only_active: bool = True,
) -> list[AllProduct]:
    q = (
        db.query(Product)
        .options(
            selectinload(Product.variants),
            selectinload(Product.images),
        )
    )

    if only_active:
        q = q.filter(Product.status == ProductStatus.ACTIVE)

    if category is not None:
        q = q.filter(Product.product_category == category)

    products = (
        q.order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    output: list[AllProduct] = []
    for product in products:
        item = AllProduct.model_validate(product)

 
        item.variants = [
            ProductVariantRead.model_validate(variant)
            for variant in product.variants
            if variant.is_active
        ]

 
        item.images = [
            ProductImageRead.model_validate(image)
            for image in sorted(product.images, key=lambda x: (x.sort_order, x.created_at))
        ]

        output.append(item)

    return output

def get_product_options(db: Session, product_id: UUID):
    variants = db.execute(
        select(ProductVariant).where(
            ProductVariant.product_id == product_id,
            ProductVariant.is_active.is_(True),
        )
    ).scalars().all()

    if not variants:
        return {
            "product_id": product_id,
            "default_variant_id": None,
            "default_price": None,
            "colors": [],
            "sizes_by_color": {},
            "variant_map": {},
            "images_by_color": {},
        }

    variants_sorted = sorted(variants, key=lambda v: str(v.id))
    default_variant = variants_sorted[0]

    images = (
        db.query(ProductImage)
        .filter(ProductImage.product_id == product_id)
        .order_by(ProductImage.sort_order.asc())
        .all()
    )

    colors = sorted({v.color for v in variants if v.color})
    sizes_by_color: dict[str, list[str]] = {}
    variant_map: dict[str, dict[str, dict]] = {}

    for v in variants:
        c = v.color or "DEFAULT"
        s = v.size or "DEFAULT"

        sizes_by_color.setdefault(c, [])
        if s not in sizes_by_color[c]:
            sizes_by_color[c].append(s)

        variant_map.setdefault(c, {})
        variant_map[c][s] = {
            "id": v.id,
            "price": v.price,
            "stock_quantity": v.stock_quantity,
            "sku": v.sku,
        }

    for c in sizes_by_color:
        sizes_by_color[c] = sorted(sizes_by_color[c])

    images_by_color: dict[str, list[dict]] = {}
    for img in images:
        c = img.color or "DEFAULT"
        images_by_color.setdefault(c, [])
        images_by_color[c].append(
            {
                "id": img.id,
                "image_url": img.image_url,
                "is_primary": img.is_primary,
                "sort_order": img.sort_order,
            }
        )

    return {
        "product_id": product_id,
        "default_variant_id": default_variant.id,
        "default_price": default_variant.price,
        "colors": colors,
        "sizes_by_color": sizes_by_color,
        "variant_map": variant_map,
        "images_by_color": images_by_color,
    }


def edit_product_by_seller(
    *,
    db: Session,
    product_id: UUID,
    product_update: ProductUpdate,
    current_seller: Seller,
) -> ProductRead:
    product = db.query(Product).filter(Product.id == product_id).one_or_none()

    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    if product.seller_id != current_seller.id:
        raise error_handler(status.HTTP_403_FORBIDDEN, "Not authorized")

    for key, value in product_update.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return ProductRead.model_validate(product)


def delete_product_by_admin(
    *,
    db: Session,
    product_id: UUID,
    current_admin: AdminProfile,
) -> dict:
    if current_admin.role_name != "Admin":
        raise error_handler(status.HTTP_403_FORBIDDEN, "Admin only")

    product = db.query(Product).filter(Product.id == product_id).one_or_none()
    if not product:
        raise error_handler(status.HTTP_404_NOT_FOUND, "Product not found")

    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}


def delete_product_by_seller(
    *,
    db: Session,
    product_id: UUID,
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


def view_all_product_seller(*, seller_id: UUID, db: Session) -> list[AllProduct]:
    products = (
        db.query(Product)
        .options(
            joinedload(Product.seller),
            selectinload(Product.variants),
            selectinload(Product.images),
        )
        .filter(
            Product.status == ProductStatus.ACTIVE,
            Product.seller_id == seller_id,
        )
        .order_by(Product.created_at.desc())
        .all()
    )
    
    output:list[AllProduct]=[]
    for product in products:
        item=AllProduct.model_validate(product)
        item.variants=[
            ProductVariantRead.model_validate(variant)
            for variant in product.variants
            if variant.is_active
        ]
        item.images = [
            ProductImageRead.model_validate(image)
            for image in sorted(product.images, key=lambda x: (x.sort_order, x.created_at))
        ]
        output.append(item)
    return output