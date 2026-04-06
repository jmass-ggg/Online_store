from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.seller import Seller
from backend.schemas.seller import (
    SellerRegister,
    SellerRegisterRead,
    SellerInforMationRead,
    SellerBusinessAddressCreate,
    SellerBusinessAddressRead,
)
from backend.service.seller_service import (
    seller_register,
    verified_seller_email,
    seller_information_fill,
    seller_information_read,
    save_upload_file,
    seller_business_address_create,
    seller_business_address_read,
)
from backend.utils.jwt import get_current_seller
from backend.utils.verifyied import verify_email_seller_or_not

router = APIRouter(prefix="/seller", tags=["Seller"])


@router.post("/apply", response_model=SellerRegisterRead)
def apply_seller(
    data: SellerRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    return seller_register(db, data, background_tasks)


@router.get("/verified-email")
def email_verified(token: str, db: Session = Depends(get_db)):
    return verified_seller_email(token, db)


@router.post("/seller-information", response_model=SellerInforMationRead)
def full_seller_information(
    legal_name: str = Form(...),
    pan_number: str = Form(...),
    account_name: str = Form(...),
    account_number: str = Form(...),
    bank_name: str = Form(...),
    branch_name: str = Form(...),
    business_document_photo: UploadFile = File(...),
    cheque_photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_email_seller_or_not),
):
    upload_folder = "backend/important_document"

    business_document_filename = save_upload_file(
        business_document_photo,
        upload_folder,
    )
    cheque_photo_filename = save_upload_file(
        cheque_photo,
        upload_folder,
    )

    return seller_information_fill(
        db=db,
        current_seller=current_seller,
        legal_name=legal_name,
        pan_number=pan_number,
        account_name=account_name,
        account_number=account_number,
        bank_name=bank_name,
        branch_name=branch_name,
        business_document_photo_filename=business_document_filename,
        cheque_photo_filename=cheque_photo_filename,
    )


@router.get("/your-information", response_model=SellerInforMationRead)
def get_your_information(
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return seller_information_read(db, current_seller)


@router.post("/business-address", response_model=SellerBusinessAddressRead)
def create_business_address(
    data: SellerBusinessAddressCreate,
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(verify_email_seller_or_not),
):
    return seller_business_address_create(db, current_seller, data)


@router.get("/business-address", response_model=SellerBusinessAddressRead)
def get_business_address(
    db: Session = Depends(get_db),
    current_seller: Seller = Depends(get_current_seller),
):
    return seller_business_address_read(db, current_seller)


@router.get("/me", response_model=SellerRegisterRead)
def get_seller(current_seller: Seller = Depends(get_current_seller)):
    return SellerRegisterRead.model_validate(current_seller)