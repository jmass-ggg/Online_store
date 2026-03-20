from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from backend.models.seller import SellerVerification


class SellerBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    business_name: str
    business_type: str = "Individual"
    business_address: str

    model_config = ConfigDict(from_attributes=True)


class SellerApplicationCreate(SellerBase):
    password: str

    kyc_document_type: str
    kyc_document_number: str

    bank_account_name: str
    bank_account_number: str
    bank_name: str
    bank_branch: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)


class SellerReviewUpdate(BaseModel):
    status: str

    model_config = ConfigDict(from_attributes=True)


class SellerResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: str

    business_name: str
    business_type: str
    business_address: str

    status: SellerVerification
    is_verified: bool

    kyc_document_type: str
    kyc_document_number: str

    bank_account_name: str
    bank_account_number: str
    bank_name: str
    bank_branch: str

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SellerUpdate(BaseModel):
    phone_number: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_address: Optional[str] = None

    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None

    kyc_document_type: Optional[str] = None
    kyc_document_number: Optional[str] = None
    kyc_document_url: Optional[str] = None

    business_license_number: Optional[str] = None
    business_license_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SellerVerificationUpdate(BaseModel):
    status: SellerVerification
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)