from fastapi import APIRouter, Depends, status, File, UploadFile, Form,Query
from sqlalchemy.orm import Session
from typing import List
from backend.core.settings import UPLOAD_DIR
from backend.models.product import ProductCategory,ProductStatus
from typing import Optional
from backend.database import get_db
from backend.schemas.product import ProductRead,ProductCreate,ProductUpdate,ProductVariantCreate,ProductVariantRead,ProductImageRead
from backend.models.seller import Seller
from backend.utils.jwt import get_current_seller,get_current_admin
from backend.utils.verifyied import verify_seller_or_not
from backend.service.product_service import (
    add_product_by_seller,
    add_product_variant,edit_product_by_seller,delete_product_by_admin,
    delete_product_by_seller,view_product,view_all_product_seller,
    view_all_product,search_products,view_product_by_slug,
    upload_single_product_image,upload_multiple_product_images

)
from backend.models.product import Product
from typing import Optional
from backend.models.admin import Admin
UPLOAD_FOLDER="backend/uploads/"
router=APIRouter(prefix="/product",tags=["Product"])

@router.get("/", response_model=List[ProductRead])
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


@router.get("/slug/{slug}", response_model=ProductRead)
def get_product_by_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    return view_product_by_slug(db, slug)

@router.get("/search", response_model=List[ProductRead])
def product_search(
    q: str = Query(..., min_length=1),
    category: Optional[ProductCategory] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return search_products(q=q, category=category, skip=skip, limit=limit, db=db)

@router.get("/{product_id}",response_model=ProductRead)
def get_product(product_id:int,db:Session=Depends(get_db),
                current_user:Seller=Depends(verify_seller_or_not)
):
    return view_product(db,product_id)

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    product_name: str = Form(...),
    url_slug: str = Form(...),
    product_category: ProductCategory = Form(...),
    description: str | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_seller_or_not),
):
    
    return add_product_by_seller(
        product_name=product_name,
        
        product_category=product_category,
        description=description,
        image=image,
        db=db,
        current_seller=current_seller,
        upload_folder=str(UPLOAD_DIR),  
    )
@router.post("/seller/products/{product_id}/image", response_model=ProductImageRead)
def upload_single_image_of_product(
    product_id: int,
    image: UploadFile = File(...),
    is_primary: bool = False,
    sort_order: int = 0,
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return upload_single_product_image(
        product_id=product_id,
        image=image,
        is_primary=is_primary,
        sort_order=sort_order,
        db=db,
        current_seller=current_seller,
    )

@router.post("/seller/products/{product_id}/images", response_model=List[ProductImageRead])
def upload_multipile_image_of_product(
    product_id: int,
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return upload_multiple_product_images(product_id, images, db, current_seller)
@router.post(
    "/{product_id}/variants",
    response_model=list[ProductVariantRead],
    status_code=status.HTTP_201_CREATED,
)
def create_product_variants(
    product_id: int,
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

    return [ProductVariantRead.from_orm(v) for v in created]

@router.patch("/{product_id}", response_model=ProductUpdate)
def product_edit(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: Seller = Depends(verify_seller_or_not)
):
    return edit_product_by_seller(db,product_id,product_update,current_user)

@router.get("/product/me", response_model=list[ProductRead])
def my_products(
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return view_all_product_seller(current_seller.id, db)

@router.delete("/{product_id}/admin",status_code=status.HTTP_200_OK)
def admin_delete_product(product_id:int,db:Session=Depends(get_db),
                current_admin:Admin=Depends(get_current_admin)
):
    return delete_product_by_admin(db,product_id,current_admin)

@router.delete("/{product_id}/seller",status_code=status.HTTP_200_OK)
def seller_delete_product(product_id:int,db:Session=Depends(get_db),
                current_user:Seller=Depends(verify_seller_or_not)
):
   return delete_product_by_seller(db, product_id, current_user)


