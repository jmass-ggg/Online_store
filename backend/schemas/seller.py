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

class SellerApplicationCreate(SellerBase):
   
    password: str

    # Optional documents
    kyc_document_type: str
    kyc_document_number: int
    kyc_document_url: str 

    
    bank_account_name: str 
    business_type:str
    business_address:str

    bank_account_name:str
    bank_account_number: int 
    bank_name: str 
    bank_branch: str 


class SellerReviewUpdate(BaseModel):
    """
    Admin updates the seller application status.
    """
    status: str            # "APPROVED" | "REJECTED"
    

class SellerResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: str

    business_name: str
    business_type: str
    business_address: str

    status: str                   # PENDING, APPROVED, REJECTED
    is_verified: bool

    kyc_document_type: str
    kyc_document_number: int
    kyc_document_url: str 

    
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
        from_attributes = True

class SellerUpdate(BaseModel):
    """
    Seller can update some info.
    Verified fields will require manual admin review.
    """
    phone_number: Optional[str] = None
    business_address: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None

    # Optional: seller can update documents to trigger re-verification
    kyc_document_type: Optional[str] = None
    kyc_document_number: Optional[str] = None
    kyc_document_url: Optional[str] = None

    business_license_number: Optional[str] = None
    business_license_url: Optional[str] = None
