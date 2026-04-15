from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.models.seller import AccountType, SellerStatus


class SellerPersonalInformationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    legal_name: str
    pan_number: str
    account_name: str
    account_number: str
    bank_name: str
    branch_name: str


class SellerRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    account_type: AccountType = AccountType.BUSINESS


class SellerPersonalInformationRead(BaseModel):
    id: UUID
    seller_id: UUID
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
    model_config = ConfigDict(extra="forbid")

    country: str = "NEPAL"
    province: str
    district: str
    area: str


class SellerBusinessAddressRead(BaseModel):
    id: UUID
    seller_id: UUID
    country: str
    province: str
    district: str
    area: str

    model_config = ConfigDict(from_attributes=True)


class SellerRegisterResponse(BaseModel):
    message: str
    user_id: UUID
    seller_id: UUID
    username: str
    email: EmailStr
    role_name: str
    account_type: str
    status: str
    is_verified: bool
    is_email_verified: bool

    model_config = ConfigDict(from_attributes=True)


class SellerRegisterRead(BaseModel):
    seller_id: UUID
    user_id: UUID
    username: str
    email: EmailStr
    account_type: str
    status: str
    is_verified: bool
    is_email_verified: bool
    role_name: str

    model_config = ConfigDict(from_attributes=True)


class SellerVerificationUpdate(BaseModel):
    status: SellerStatus
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class SellerDetail(BaseModel):
    seller_detail: SellerRegisterRead
    seller_information: list[SellerPersonalInformationRead]
    seller_address: list[SellerBusinessAddressRead]

    model_config = ConfigDict(from_attributes=True)