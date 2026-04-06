from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from backend.models.role import RoleChoices
from backend.models.seller import SellerVerification, AccountType


class SellerRegister(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    hash_password: str
    account_type: AccountType


class SellerRegisterRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    phone_number: str
    account_type: str
    status: str
    is_verified: bool
    is_email_verified: bool
    role_name: str

    model_config = ConfigDict(from_attributes=True)


class SellerInforMation(BaseModel):
    legal_name: str
    pan_number: str
    account_name: str
    account_number: str
    bank_name: str
    branch_name: str

    model_config = ConfigDict(from_attributes=True)


class SellerInforMationRead(BaseModel):
    id: UUID
    user_id: UUID
    legal_name: str
    pan_number: str
    business_document_photo: str
    account_name: str
    account_number: str
    bank_name: str
    branch_name: str
    cheque_photo: str

    model_config = ConfigDict(from_attributes=True)


class SellerBusinessAddressCreate(BaseModel):
    country: str = "NEPAL"
    province: str
    district: str
    area: str

    model_config = ConfigDict(from_attributes=True)


class SellerBusinessAddressRead(BaseModel):
    id: UUID
    user_id: UUID
    country: str
    province: str
    district: str
    area: str

    model_config = ConfigDict(from_attributes=True)


class SellerVerificationUpdate(BaseModel):
    status: SellerVerification
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)