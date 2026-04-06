from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr
from backend.models.role import RoleChoices
from backend.models.seller import SellerVerification,AccountType


class SellerRegister(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    hash_password:str
    account_type:AccountType
    
class SellerRegisterRead(BaseModel):
    id:UUID
    username: str
    email: EmailStr
    phone_number: str
    account_type:str
    status:str
    is_verified:bool
    is_email_verified:bool
    role_name:str
    
    
    
    model_config = ConfigDict(from_attributes=True)

class SellerInforMation(BaseModel):
    legal_name:str
    pan_number:str
    
    account_name:str
    account_number:str
    bank_name:str
    branch_name:str
    
    model_config = ConfigDict(from_attributes=True)

class SellerInforMationRead(BaseModel):
    id:UUID
    user_id:UUID
    legal_name:str
    pan_number:str
    business_document_photo:str
    account_name:str
    account_number:str
    bank_name:str
    branch_name:str
    cheque_photo:str
    model_config = ConfigDict(from_attributes=True)
    
class SellerBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    business_name: str
    business_type:Optional[str] = "Individual"
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
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class SellerReviewUpdate(BaseModel):
    status: SellerVerification

    model_config = ConfigDict(from_attributes=True)


class SellerResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    phone_number: str

    business_name: str
    business_type: str
    business_address: str

    status: SellerVerification
    is_verified: bool

    kyc_document_type: Optional[str] = None
    kyc_document_number: Optional[str] = None

    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    role_name:RoleChoices
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