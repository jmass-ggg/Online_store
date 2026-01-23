from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class SellerBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    business_name: str
    business_type: Optional[str] = "Individual"
    business_address: str
    class Config:
        orm_mode = True
        from_attributes = True

class SellerApplicationCreate(SellerBase):
   
    password: str

    business_name: str 
    business_type:str
    business_address:str

    kyc_document_type: str
    kyc_document_number: int

    bank_account_name:str
    bank_account_number: int 
    bank_name: str 
    bank_branch: str 
    class Config:
        orm_mode = True
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str 

class SellerReviewUpdate(BaseModel):
    
    status: str            # "APPROVED" "REJECTED"
    class Config:
        orm_mode = True
        from_attributes = True

class SellerResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: str

    status: str                   # PENDING, APPROVED, REJECTED
    is_verified: bool

    kyc_document_type: str
    kyc_document_number: int

    bank_account_name: str 
    business_type:str
    business_address:str

    bank_account_name:str
    bank_account_number: int 
    bank_name: str 
    bank_branch: str

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class SellerUpdate(BaseModel):

    phone_number: Optional[str] = None
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
    class Config:
        orm_mode = True
        from_attributes = True

class SellerVerificationUpdate(BaseModel):
    status:str
    is_verified:bool
    class Config:
        orm_mode = True
        from_attributes = True