from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from fastapi_cache.decorator import cache
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.admin import AdminProfile
from backend.models.product import ProductCategory, TargetAudience
from backend.models.seller import Seller
from backend.schemas.product import (
    AllProduct,
    ProductImageRead,
    ProductImageUpdate,
    ProductListRead,
    ProductRead,
    ProductUpdate,
    ProductVariantCreate,
    ProductVariantRead,
)
from backend.service.product_service import (
    add_product_by_seller,
    add_product_variant,
    delete_product_by_admin,
    delete_product_by_seller,
    edit_product_by_seller,
    get_product_options,
    search_products,
    update_product_image,
    upload_multiple_product_images,
    upload_single_product_image,
    view_all_product,
    view_all_product_seller,
    view_product,
    view_product_by_slug,
)
from backend.utils.jwt import get_current_admin, get_current_seller
from backend.utils.verifyied import verify_seller_or_not

router = APIRouter(prefix="/product", tags=["Product"])


def product_cache_key_builder(
    func,
    namespace: str = "",
    *,
    request: Request = None,
    response: Response = None,
    args=(),
    kwargs=None,
):
    if request:
        return f"{namespace}:{request.method}:{request.url.path}:{dict(request.query_params)}"
    return f"{namespace}:product-list"


@router.get("/", response_model=List[ProductListRead])
@cache(expire=120, key_builder=product_cache_key_builder)
def get_all_product(
    category: Optional[ProductCategory] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return view_all_product(
        db=db,
        category=category,
        skip=skip,
        limit=limit,
        only_active=True,
    )


@router.get("/search", response_model=List[ProductRead])
def product_search(
    q: str = Query(..., min_length=1),
    category: Optional[ProductCategory] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return search_products(
        q=q,
        category=category,
        skip=skip,
        limit=limit,
        db=db,
    )


@router.get("/slug/{slug}", response_model=AllProduct)
def get_product_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    return view_product_by_slug(db, slug)


@router.get("/seller/me", response_model=list[ProductRead])
def my_products(
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return view_all_product_seller(seller_id=current_seller.id, db=db)


@router.get("/products/{product_id}/options")
def product_options(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    return get_product_options(db, product_id)


@router.get("/{product_id}", response_model=AllProduct)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
):
    return view_product(db, product_id)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    product_name: str = Form(...),
    target_audience: TargetAudience = Form(...),
    product_category: ProductCategory = Form(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    return add_product_by_seller(
        product_name=product_name,
        target_audience=target_audience,
        product_category=product_category,
        description=description,
        db=db,
        current_seller=current_seller,
    )


@router.post("/{product_id}/images", response_model=list[ProductImageRead], status_code=status.HTTP_201_CREATED)
def upload_product_images(
    product_id: UUID,
    images: list[UploadFile] = File(...),
    color: str | None = Form(None),
    primary_index: int | None = Form(None),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    return upload_multiple_product_images(
        product_id=product_id,
        images=images,
        color=color,
        primary_index=primary_index,
        db=db,
        current_seller=current_seller,
    )


@router.post("/{product_id}/image", response_model=ProductImageRead, status_code=status.HTTP_201_CREATED)
def upload_product_image(
    product_id: UUID,
    image: UploadFile = File(...),
    color: str | None = Form(None),
    is_primary: bool | None = Form(None),
    sort_order: int | None = Form(None),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    return upload_single_product_image(
        product_id=product_id,
        image=image,
        color=color,
        is_primary=is_primary,
        sort_order=sort_order,
        db=db,
        current_seller=current_seller,
    )


@router.patch("/images/{image_id}", response_model=ProductImageRead)
def patch_product_image(
    image_id: UUID,
    image_update: ProductImageUpdate,
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    return update_product_image(
        image_id=image_id,
        data=image_update,
        db=db,
        current_seller=current_seller,
    )


@router.post("/{product_id}/variants", response_model=list[ProductVariantRead], status_code=status.HTTP_201_CREATED)
def create_product_variants(
    product_id: UUID,
    variants: list[ProductVariantCreate],
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    created = add_product_variant(
        db=db,
        product_id=product_id,
        variants=variants,
        current_seller=current_seller,
    )
    return [ProductVariantRead.model_validate(variant) for variant in created]


@router.patch("/{product_id}", response_model=ProductRead)
def product_edit(
    product_id: UUID,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    return edit_product_by_seller(
        db=db,
        product_id=product_id,
        product_update=product_update,
        current_seller=current_seller,
    )


@router.delete("/{product_id}/admin", status_code=status.HTTP_200_OK)
def admin_delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_admin: AdminProfile = Depends(get_current_admin),
):
    return delete_product_by_admin(
        db=db,
        product_id=product_id,
        current_admin=current_admin,
    )


@router.delete("/{product_id}/seller", status_code=status.HTTP_200_OK)
def seller_delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    return delete_product_by_seller(
        db=db,
        product_id=product_id,
        current_seller=current_seller,
    )