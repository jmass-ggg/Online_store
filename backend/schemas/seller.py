from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# -----------------------------
# SHARED BASE
# -----------------------------
class SellerBase(BaseModel):
    username: str
    email: EmailStr
    phone_number: str
    business_name: str
    business_type: Optional[str] = "Individual"
    business_address: str

# -----------------------------
# 1) SELLER APPLICATION (SUBMISSION)
# -----------------------------
class SellerApplicationCreate(SellerBase):
    """
    Seller submits this application.
    Status will be PENDING until admin reviews.
    """
    password: str

    # Optional documents
    kyc_document_type: Optional[str] = None
    kyc_document_number: Optional[str] = None
    kyc_document_url: Optional[str] = None

    business_license_number: Optional[str] = None
    business_license_url: Optional[str] = None
    
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch: Optional[str] = None


# -----------------------------
# 2) APPLICATION REVIEW (ADMIN ACTION)
# -----------------------------
class SellerReviewUpdate(BaseModel):
    """
    Admin updates the seller application status.
    """
    status: str            # "APPROVED" | "REJECTED"
    


# -----------------------------
# 3) INTERNAL SELLER MODEL RESPONSE
# -----------------------------
class SellerResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: str

    business_name: str
    business_type: str
    business_address: str

    # Status managed by admin
    status: str                   # PENDING, APPROVED, REJECTED
    is_verified: bool

    # KYC
    kyc_document_type: Optional[str]
    kyc_document_number: Optional[str]
    kyc_document_url: Optional[str]

    # Business Documents
    business_license_number: Optional[str]
    business_license_url: Optional[str]

    # Banking
    bank_account_name: Optional[str]
    bank_account_number: Optional[str]
    bank_name: Optional[str]
    bank_branch: Optional[str]

    rating: float
    total_sales: int

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -----------------------------
# 4) SELLER UPDATE PROFILE (POST-APPROVAL)
# -----------------------------
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
